import pytest
from qm import ControllerConnection, InterOpxChannel

from qualang_tools.simulator_tools import create_simulator_controller_connections


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
    generated_controller_connections = create_simulator_controller_connections(2, 12)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_three_controllers_connection_schema():
    first_controller_list = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2]
    first_port_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 6, 7, 8, 9, 10, 11]
    second_controller_list = [2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    second_port_list = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
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
    generated_controller_connections = create_simulator_controller_connections(3, 12)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_four_controllers_connection_schema():
    first_controller_list = [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
    ]
    first_port_list = [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        8,
        9,
        10,
        11,
    ]
    second_controller_list = [
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
        4,
    ]
    second_port_list = [
        0,
        1,
        2,
        3,
        0,
        1,
        2,
        3,
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
    ]
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
    generated_controller_connections = create_simulator_controller_connections(4, 12)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_five_controllers_connection_schema():
    first_controller_list = [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
    ]
    first_port_list = [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        6,
        7,
        8,
        9,
        10,
        11,
        9,
        10,
        11,
    ]
    second_controller_list = [
        2,
        2,
        2,
        3,
        3,
        3,
        4,
        4,
        4,
        5,
        5,
        5,
        3,
        3,
        3,
        4,
        4,
        4,
        5,
        5,
        5,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
        5,
        5,
    ]
    second_port_list = [
        0,
        1,
        2,
        0,
        1,
        2,
        0,
        1,
        2,
        0,
        1,
        2,
        3,
        4,
        5,
        3,
        4,
        5,
        3,
        4,
        5,
        6,
        7,
        8,
        6,
        7,
        8,
        9,
        10,
        11,
    ]
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
    generated_controller_connections = create_simulator_controller_connections(5, 12)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_six_controllers_connection_schema():
    first_controller_list = [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        5,
        5,
    ]
    first_port_list = [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        4,
        5,
        6,
        7,
        8,
        9,
        6,
        7,
        8,
        9,
        8,
        9,
    ]
    second_controller_list = [
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
        3,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
        4,
        4,
        5,
        5,
        6,
        6,
        5,
        5,
        6,
        6,
        6,
        6,
    ]
    second_port_list = [
        0,
        1,
        0,
        1,
        0,
        1,
        0,
        1,
        0,
        1,
        2,
        3,
        2,
        3,
        2,
        3,
        2,
        3,
        4,
        5,
        4,
        5,
        4,
        5,
        6,
        7,
        6,
        7,
        8,
        9,
    ]
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
    generated_controller_connections = create_simulator_controller_connections(6, 12)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)


def test_ten_controllers_connection_schema():
    first_controller_list = [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
        5,
        6,
        6,
        6,
        6,
        7,
        7,
        7,
        8,
        8,
        9,
    ]
    first_port_list = [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        3,
        4,
        5,
        6,
        7,
        8,
        4,
        5,
        6,
        7,
        8,
        5,
        6,
        7,
        8,
        6,
        7,
        8,
        7,
        8,
        8,
    ]
    second_controller_list = [
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        5,
        6,
        7,
        8,
        9,
        10,
        6,
        7,
        8,
        9,
        10,
        7,
        8,
        9,
        10,
        8,
        9,
        10,
        9,
        10,
        10,
    ]
    second_port_list = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
        6,
        6,
        6,
        7,
        7,
        8,
    ]
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
    generated_controller_connections = create_simulator_controller_connections(10, 12)
    assert len(controller_connections) == len(generated_controller_connections)
    for a, b in zip(controller_connections, generated_controller_connections):
        assert (a.source == b.source) & (a.target == b.target)
