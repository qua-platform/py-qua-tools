import numpy as np
from qm import ControllerConnection, InterOpxChannel


def create_simulator_controller_connections(n_controllers, n_connections=12, old_method=False, n_actual_controllers=None):
    """
    Creates a list of :class:`~qm.simulate.interface.ControllerConnection` objects with all of the Inter-controllers
    connections according to the `recommended schema
    <https://qm-docs.qualang.io/hardware/opx+installation#inter-controller-optical-connectivity-scheme>`__.
    For use inside the :class:`~qm.simulate.interface.SimulationConfig` for simulating the controllers` behavior.

    :param n_controllers: The number of controllers
    :type n_controllers: int
    :param n_connections: The number of optical connectors each controller has, default is 12
    :type n_connections: int
    :returns: The ControllerConnection object

    """
    if not old_method:
        if not n_actual_controllers:
            n_actual_controllers = n_controllers
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
                    if i < n_actual_controllers and j < n_actual_controllers:
                        controller_connections.append(
                            ControllerConnection(
                                InterOpxChannel(f"con{i+1}", first_con_port),
                                InterOpxChannel(f"con{j+1}", second_con_port))
                        )
                    print(f"con{i+1}:{first_con_port} <-> con{j+1}, {second_con_port}")
                    unused_connection[i, first_con_port] = False
                    unused_connection[j, second_con_port] = False
    else:
        ncbc = n_connections // (
            n_controllers - 1
        )  # ncbc = number_of_connections_between_controllers
        n_connections = ncbc * (n_controllers - 1)
        first_controller_list = []
        first_port_list = []
        second_controller_list = []
        second_port_list = []
        for i in range(n_controllers):
            first_controller_list = first_controller_list + [i + 1] * (
                n_connections - i * ncbc
            )

            first_port_list = first_port_list + [j for j in range(i * ncbc, n_connections)]

            for j in range(i + 1, n_controllers):
                second_controller_list = second_controller_list + [j + 1] * ncbc

            second_port_list = second_port_list + [
                j for j in range(i * ncbc, (i + 1) * ncbc)
            ] * (n_controllers - i - 1)

        controller_connections = [
            ControllerConnection(
                InterOpxChannel(f"con{i}", j), InterOpxChannel(f"con{k}", l)
            )
            for i, j, k, l in list(
                zip(
                    first_controller_list,
                    first_port_list,
                    second_controller_list,
                    second_port_list,
                )
            )
        ]

    return controller_connections
