# %% Imports
from qualang_tools.control_panel.video_mode.plotly_tools import *
import numpy as np
from qualang_tools.control_panel.video_mode.voltage_parameters import *
from qualang_tools.control_panel.video_mode.data_acquirers import *
from qualang_tools.control_panel.video_mode.video_mode import *

from quam.components import BasicQuAM, SingleChannel, InOutSingleChannel, pulses

from qm import QuantumMachinesManager

import logging

# Update the logging configuration
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("hpack.hpack").setLevel(logging.WARNING)

# %% Create config and connect to QM
machine = BasicQuAM()

machine.channels["LP"] = SingleChannel(opx_output=("con1", 10))
machine.channels["RP"] = SingleChannel(opx_output=("con1", 8))
machine.channels["bottom_left_DQD_readout"] = InOutSingleChannel(
    opx_output=("con1", 9),
    opx_input=("con1", 2),
    intermediate_frequency=140555556,
    time_of_flight=260,
    smearing=0,
    operations={"readout": pulses.SquareReadoutPulse(length=20000, amplitude=0.1)},
)

qmm = QuantumMachinesManager(host="192.168.8.4", cluster_name="Cluster_1")
# qmm = machine.connect()
config = machine.generate_config()

# Open the quantum machine
qm = qmm.open_qm(config, close_other_machines=True)


# %% Run OPXDataAcquirer
from qualang_tools.control_panel.video_mode.scan_modes import raster_scan
from qualang_tools.control_panel.video_mode.inner_loop_actions import InnerLoopActionQuam

x_offset = VoltageParameter(name="X Voltage Offset", initial_value=0.0)
y_offset = VoltageParameter(name="Y Voltage Offset", initial_value=0.0)
inner_loop_action = InnerLoopActionQuam(
    x_element=machine.channels["ch1"],
    y_element=machine.channels["ch2"],
    readout_element=machine.channels["ch_readout"],
    readout_pulse="readout",
)

data_acquirer = OPXDataAcquirer(
    qm=qm,
    qua_inner_loop_action=inner_loop_action,
    scan_function=raster_scan,
    x_offset_parameter=x_offset,
    y_offset_parameter=y_offset,
    x_span=0.05,
    y_span=0.05,
    num_averages=5,
    x_points=101,
    y_points=101,
    integration_time=20e-6,
    final_delay=30e-3,
)
# %% Run program
data_acquirer.stream_vars = ["I", "Q"]
data_acquirer.run_program(verify=True)

# %%
results = data_acquirer.acquire_data()
print(f"Mean of results: {np.mean(np.abs(results))}")


# %%
live_plotter = VideoMode(data_acquirer=data_acquirer, update_interval=1)
live_plotter.run(use_reloader=False)

# %%
