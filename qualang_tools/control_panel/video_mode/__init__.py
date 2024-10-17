from qualang_tools.control_panel.video_mode.dash_tools import *
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
from qualang_tools.control_panel.video_mode.voltage_parameters import *
from qualang_tools.control_panel.video_mode.inner_loop_actions import *
from qualang_tools.control_panel.video_mode.scan_modes import *
from qualang_tools.control_panel.video_mode.data_acquirers import *
from qualang_tools.control_panel.video_mode.video_mode import *


if __name__ == "__main__":
    x_axis = SweepAxis(name="X", span=0.1, points=101)
    y_axis = SweepAxis(name="Y", span=0.1, points=101)

    data_acquirer = RandomDataAcquirer(
        x_axis=x_axis,
        y_axis=y_axis,
        num_averages=5,
    )

    live_plotter = VideoMode(data_acquirer=data_acquirer)
    live_plotter.run()
