from qualang_tools.plot.video_mode.plotly_tools import *
from qualang_tools.plot.video_mode.voltage_parameters import *
from qualang_tools.plot.video_mode.data_acquirers import *
from qualang_tools.plot.video_mode.video_mode import *


if __name__ == "__main__":
    x_offset = VoltageParameter(name="X Voltage Offset", initial_value=0.0)
    y_offset = VoltageParameter(name="Y Voltage Offset", initial_value=0.0)
    x_span = 0.1
    y_span = 0.1

    data_acquirer = RandomDataAcquirer(
        x_offset_parameter=x_offset,
        y_offset_parameter=y_offset,
        x_span=x_span,
        y_span=y_span,
        num_averages=5,
        x_points=101,
        y_points=101,
    )

    live_plotter = VideoMode(data_acquirer=data_acquirer, integration_time=10e-6)
    live_plotter.run()
