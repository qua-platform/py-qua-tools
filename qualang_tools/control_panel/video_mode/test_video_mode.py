# %% Imports
from qualang_tools.control_panel.video_mode.dash_tools import *
import numpy as np
from matplotlib import pyplot as plt
from qualang_tools.control_panel.video_mode.voltage_parameters import *
from qualang_tools.control_panel.video_mode.sweep_axis import *
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
readout_pulse = pulses.SquareReadoutPulse(id="readout", length=1000, amplitude=0.1)
machine.channels["ch_readout"] = InOutSingleChannel(
    opx_output=("con1", 3),
    opx_input=("con1", 1),
    intermediate_frequency=100e6,
    operations={"readout": readout_pulse},
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
    readout_pulse=readout_pulse,
)

scan_mode = SpiralScan()
data_acquirer = OPXDataAcquirer(
    qm=qm,
    qua_inner_loop_action=inner_loop_action,
    scan_mode=scan_mode,
    x_axis=SweepAxis("x", span=0.03, points=11, offset_parameter=x_offset),
    y_axis=SweepAxis("y", span=0.03, points=11, offset_parameter=y_offset),
    result_type="abs",
)
# %% Run program
data_acquirer.run_program()

# %%
results = data_acquirer.acquire_data()
print(f"Mean of results: {np.mean(np.abs(results))}")


# %%
live_plotter = VideoMode(data_acquirer=data_acquirer, update_interval=1)
live_plotter.run(use_reloader=False)

# %%
scan_mode.plot_scan(11, 11)

# %% Generate QUA script
from qm import generate_qua_script

qua_script = generate_qua_script(data_acquirer.generate_program(), config)
print(qua_script)

# %% Simulate results
from qm import SimulationConfig

prog = data_acquirer.generate_program()
simulation_config = SimulationConfig(duration=100000)  # In clock cycles = 4ns
job = qmm.simulate(config, prog, simulation_config)
con1 = job.get_simulated_samples().con1

con1.plot(analog_ports=["1", "2"])

plt.figure()
plt.plot(con1.analog["1"], con1.analog["2"])

plt.figure()
data_acquirer.scan_mode.plot_scan(data_acquirer.x_axis.points, data_acquirer.y_axis.points)

# %%
from qualang_tools.control_panel.video_mode.scan_modes import SwitchRasterScan
import numpy as np
scan_mode = SwitchRasterScan()
print(scan_mode.interleave_arr(np.arange(10)))
scan_mode.plot_scan(10, 10)
# %%
