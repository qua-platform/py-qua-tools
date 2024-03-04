from qm import ControllerConnection, InterOpxChannel

from qualang_tools.simulator import create_simulator_controller_connections


def test_two_controllers_connection_schema():
    first_controller_list = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    first_port_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    second_controller_list = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
    second_port_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
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
    generated_controller_connections = create_simulator_controller_connections(2)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_three_controllers_connection_schema():
    first_controller_list = [1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2]
    first_port_list = [0, 1, 1, 2, 3, 3, 4, 5, 5, 6, 7, 7, 8, 9, 9, 10, 11, 11]
    second_controller_list = [2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3]
    second_port_list = [0, 0, 1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 8, 8, 9, 10, 10, 11]
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
    generated_controller_connections = create_simulator_controller_connections(3)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_last_two_in_a_three_controllers_connection_schema():
    first_controller_list = [1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2]
    first_port_list = [0, 1, 1, 2, 3, 3, 4, 5, 5, 6, 7, 7, 8, 9, 9, 10, 11, 11]
    second_controller_list = [2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3]
    second_port_list = [0, 0, 1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 8, 8, 9, 10, 10, 11]
    filtered_lists = [(item1, item2, item3, item4) for item1, item2, item3, item4 in zip(first_controller_list, first_port_list, second_controller_list, second_port_list) if item1 != 1 and item3 != 1]
    first_controller_list, first_port_list, second_controller_list, second_port_list = zip(*filtered_lists)
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
    generated_controller_connections = create_simulator_controller_connections(3, [2, 3])
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_two_in_a_three_controllers_connection_schema():
    first_controller_list = [1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2]
    first_port_list = [0, 1, 1, 2, 3, 3, 4, 5, 5, 6, 7, 7, 8, 9, 9, 10, 11, 11]
    second_controller_list = [2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 3, 3]
    second_port_list = [0, 0, 1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 8, 8, 9, 10, 10, 11]
    filtered_lists = [(item1, item2, item3, item4) for item1, item2, item3, item4 in zip(first_controller_list, first_port_list, second_controller_list, second_port_list) if item1 != 2 and item3 != 2]
    first_controller_list, first_port_list, second_controller_list, second_port_list = zip(*filtered_lists)
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
    generated_controller_connections = create_simulator_controller_connections(3, [1, 3])
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)
