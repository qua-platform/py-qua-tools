from qualang_tools.control_panel.video_mode.dash_tools import *
from qualang_tools.control_panel.video_mode.sweep_axis import SweepAxis
from qualang_tools.control_panel.video_mode.voltage_parameters import *
from qualang_tools.control_panel.video_mode.inner_loop_actions import *
from qualang_tools.control_panel.video_mode.scan_modes import *
from qualang_tools.control_panel.video_mode.data_acquirers import *
from qualang_tools.control_panel.video_mode.video_mode import *


if __name__ == "__main__":
    import logging

    # Update the logging configuration
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("hpack.hpack").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    x_axis = SweepAxis(name="X", span=0.1, points=101)
    y_axis = SweepAxis(name="Y", span=0.1, points=101)

    data_acquirer = RandomDataAcquirer(
        x_axis=x_axis,
        y_axis=y_axis,
        num_averages=5,
        acquire_time=0.1,
    )

    live_plotter = VideoMode(data_acquirer=data_acquirer, update_interval=0.1)
    live_plotter.run()
