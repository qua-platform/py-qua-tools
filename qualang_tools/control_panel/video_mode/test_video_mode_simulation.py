from qualang_tools.control_panel.video_mode.dash_tools import *
from qualang_tools.control_panel.video_mode.voltage_parameters import *
from qualang_tools.control_panel.video_mode.data_acquirers import *
from qualang_tools.control_panel.video_mode.video_mode import *
import logging

logging.basicConfig(level=logging.DEBUG)

x_offset = VoltageParameter(name="X Voltage Offset", initial_value=0.0)
y_offset = VoltageParameter(name="Y Voltage Offset", initial_value=0.0)

data_acquirer = RandomDataAcquirer(
    x_offset_parameter=x_offset,
    y_offset_parameter=y_offset,
    x_span=0.1,
    y_span=0.1,
    num_averages=5,
    x_points=101,
    y_points=101,
    integration_time=10e-6,
)

live_plotter = VideoMode(data_acquirer=data_acquirer)
live_plotter.run()
