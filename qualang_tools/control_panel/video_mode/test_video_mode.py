# %% Imports
from qualang_tools.control_panel.video_mode.plotly_tools import *
import numpy as np
from matplotlib import pyplot as plt
from qualang_tools.control_panel.video_mode.voltage_parameters import *
from qualang_tools.control_panel.video_mode.data_acquirers import *
from qualang_tools.control_panel.video_mode.video_mode import *

from quam.components import BasicQuAM, SingleChannel, InOutSingleChannel, pulses

from qm import QuantumMachinesManager

import logging

# Update the logging configuration
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("hpack.hpack").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

# %% Create config and connect to QM
machine = BasicQuAM()

machine.channels["ch1"] = SingleChannel(opx_output=("con1", 1))
machine.channels["ch2"] = SingleChannel(opx_output=("con1", 2))
machine.channels["ch_readout"] = InOutSingleChannel(
    opx_output=("con1", 3),
    opx_input=("con1", 1),
    intermediate_frequency=100e6,
    operations={"readout": pulses.SquareReadoutPulse(length=1000, amplitude=0.1)},
)

qmm = QuantumMachinesManager(host="192.168.8.4", cluster_name="Cluster_1")
# qmm = machine.connect()
config = machine.generate_config()

# Open the quantum machine
qm = qmm.open_qm(config, close_other_machines=True)


# %% Run OPXDataAcquirer
from qualang_tools.control_panel.video_mode.scan_modes import RasterScan, SpiralScan
from qualang_tools.control_panel.video_mode.inner_loop_actions import InnerLoopActionQuam

x_offset = VoltageParameter(name="X Voltage Offset", initial_value=0.0)
y_offset = VoltageParameter(name="Y Voltage Offset", initial_value=0.0)
inner_loop_action = InnerLoopActionQuam(
    x_element=machine.channels["ch1"],
    y_element=machine.channels["ch2"],
    readout_element=machine.channels["ch_readout"],
    readout_pulse="readout",
    integration_time=machine.channels["ch_readout"].operations["readout"].length,
)
# scan_mode = RasterScan()
scan_mode = SpiralScan()
data_acquirer = OPXDataAcquirer(
    qm=qm,
    qua_inner_loop_action=inner_loop_action,
    scan_mode=scan_mode,
    x_offset_parameter=x_offset,
    y_offset_parameter=y_offset,
    x_span=0.02,
    y_span=0.02,
    x_attenuation=0,
    y_attenuation=0,
    num_averages=5,
    x_points=11,
    y_points=11,
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
scan_mode.plot_scan(np.arange(11), np.arange(11))

# %% Generate QUA script
from qm import generate_qua_script

qua_script = generate_qua_script(data_acquirer.generate_program(), config)
print(qua_script)

# %% Simulate results
from qm import SimulationConfig

prog = data_acquirer.generate_program()
simulation_config = SimulationConfig(duration=30000)  # In clock cycles = 4ns
job = qmm.simulate(config, prog, simulation_config)
con1 = job.get_simulated_samples().con1

con1.plot(analog_ports=["1", "2"])

plt.figure()
plt.plot(con1.analog["1"], con1.analog["2"])

# %%
