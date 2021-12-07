from qm import ControllerConnection, InterOpxChannel


def create_controller_connections(number_of_controllers, connections=12):
    """
    Creates a list of :class:`~qm.simulate.interface.ControllerConnection` objects with all of the Inter-controllers
    connections according to the `recommended schema
    <https://qm-docs.qualang.io/hardware/opx+installation#inter-controller-optical-connectivity-scheme>`__.
    For use inside the :class:`~qm.simulate.interface.SimulationConfig` for simulating the controllers` behavior.

    :param number_of_controllers: The number of controllers
    :param connections: The number of optical connectors each controller has, default is 12.

    """
    connections_per_controller = connections // (number_of_controllers - 1)
    connections = connections_per_controller * (number_of_controllers - 1)
    first_controller_list = []
    first_port_list = []
    second_controller_list = []
    second_port_list = []
    for i in range(number_of_controllers):
        first_controller_list = first_controller_list + [i + 1] * (
            connections - i * connections_per_controller
        )
        first_port_list = first_port_list + [
            j for j in range(i * connections_per_controller, connections)
        ]
        for j in range(i + 1, number_of_controllers):
            second_controller_list = (
                second_controller_list + [j + 1] * connections_per_controller
            )
        second_port_list = second_port_list + +[
            j
            for j in range(
                i * connections_per_controller, (i + 1) * connections_per_controller
            )
        ] * (number_of_controllers - i - 1)

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
