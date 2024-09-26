from typing import Sequence, Callable

from qm.qua import declare, declare_stream, save, assign, from_array, for_


def raster_scan(
    x_vals: Sequence[float],
    y_vals: Sequence[float],
    qua_inner_loop_action: Callable,
    idxs_streams: dict,
    voltages_streams: dict,
    IQ_streams: dict,
):
    idxs = {"x": declare(int), "y": declare(int)}
    voltages = {"x": declare_stream(), "y": declare_stream()}

    assign(idxs["x"], 0)
    with for_(*from_array(voltages["x"], x_vals)):  # type: ignore
        save(idxs["x"], idxs_streams["x"])
        save(voltages["x"], voltages_streams["x"])

        assign(idxs["y"], 0)
        with for_(*from_array(voltages["y"], y_vals)):  # type: ignore
            save(idxs["y"], idxs_streams["y"])
            save(voltages["y"], voltages_streams["y"])

            I, Q = qua_inner_loop_action(idxs, voltages)
            save(I, IQ_streams["I"])
            save(Q, IQ_streams["Q"])

            assign(idxs["y"], idxs["y"] + 1)  # type: ignore
        assign(idxs["x"], idxs["x"] + 1)  # type: ignore


def spiral_scan(
    x_vals: Sequence[float],
    y_vals: Sequence[float],
    qua_inner_loop_action: Callable,
    idxs_streams: dict,
    voltages_streams: dict,
    IQ_streams: dict,
):
    idxs = {"x": declare(int), "y": declare(int)}
    idxs_pm = {"x": declare(int), "y": declare(int)}
    idx_offset = int((self.x_points - 1) / 2)

    voltages = {"x": declare_stream(), "y": declare_stream()}

    voltages_streams = {"x": declare_stream(), "y": declare_stream()}
    idxs_streams = {"x": declare_stream(), "y": declare_stream()}
    IQ_streams = {"I": declare_stream(), "Q": declare_stream()}

    num_spiral = declare(int)
    num_spirals = 4

    assert self.x_points == self.y_points, "Spiral only works for square grids"
    assert self.x_points % 2 == 1, "Spiral only works for odd number of points"

    with for_(num_spiral, 0, num_spiral < num_spirals, num_spiral + 1):
        for move_axis in "xy":
            with for_(idxs_pm[move_axis], 0, idxs_pm[move_axis] < num_spiral, idxs_pm[move_axis] + 1):
                for axis in "xy":
                    save(idxs[axis], idxs_streams[axis])
                    save(voltages[axis], voltages_streams[axis])

                qua_inner_loop_action(axis)

    # for_ loop to move the required number of moves in the x direction
    with for_(i, 0, i < moves_per_edge, i + 1):
        assign(x, x + movement_direction * x_step_size * 0.5)  # updating the x location
        save(x, x_st)
        save(y, y_st)

    # for_ loop to move the required number of moves in the y direction
    with for_(j, 0, j < moves_per_edge, j + 1):
        assign(y, y + movement_direction * y_step_size * 0.5)
        save(x, x_st)
        save(y, y_st)
