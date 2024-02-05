import numpy as np
from qm import ControllerConnection, InterOpxChannel


def create_simulator_controller_connections(
    n_controllers, actual_controllers=None, n_connections=12, print_debug=False
):
    """
    Creates a list of :class:`~qm.simulate.interface.ControllerConnection` objects with the Inter-controllers
    connections between controllers in a way which maximizes the optical links connectivity.
    For use inside the :class:`~qm.simulate.interface.SimulationConfig` for simulating the controllers` behavior.

    :param n_controllers: The number of controllers
    :type n_controllers: int
    :param actual_controllers: A list of the controllers actually being used in the simulation. For `con1` & `con2` use [1,2].
    :type actual_controllers: List[int]
    :param n_connections: The number of optical connectors each controller has, default is 12
    :type n_connections: int
    :param print_debug: If true, prints the connections to the terminal
    :type print_debug: bool
    :returns: The ControllerConnection object

    """
    if n_controllers == 1:
        return []
    if not actual_controllers:
        actual_controllers = [i + 1 for i in range(n_controllers)]
    controller_connections = []
    unused_connection = np.ones((n_controllers, n_connections), dtype=bool)
    while unused_connection.any():
        for i in range(n_controllers):
            for j in range(i + 1, n_controllers):
                first_con_port = np.nonzero(unused_connection[i, :])[0]
                if first_con_port.size == 0:
                    break
                first_con_port = first_con_port[0]
                second_con_port = np.nonzero(unused_connection[j, :])[0]
                if second_con_port.size == 0:
                    break
                second_con_port = second_con_port[0]
                if i + 1 in actual_controllers and j + 1 in actual_controllers:
                    controller_connections.append(
                        ControllerConnection(
                            InterOpxChannel(f"con{i+1}", first_con_port), InterOpxChannel(f"con{j+1}", second_con_port)
                        )
                    )
                    if print_debug:
                        print(f"con{i + 1}:{first_con_port} <-> con{j + 1}, {second_con_port}")
                elif print_debug:
                    print(f"con{i + 1}:{first_con_port} <-> con{j + 1}, {second_con_port} - Skipped")
                unused_connection[i, first_con_port] = False
                unused_connection[j, second_con_port] = False

    return controller_connections
