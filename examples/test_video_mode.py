# %% Imports
import logging
from qualang_tools.control_panel.video_mode.dash_tools import *
from matplotlib import pyplot as plt

from qualang_tools.control_panel.video_mode.voltage_parameters import *
from qualang_tools.control_panel.video_mode.sweep_axis import *
from qualang_tools.control_panel.video_mode.data_acquirers import *
from qualang_tools.control_panel.video_mode.video_mode import *
from qualang_tools.control_panel.video_mode import scan_modes
from qualang_tools.control_panel.video_mode.inner_loop_actions import BasicInnerLoopActionQuam

from qm import QuantumMachinesManager

from quam.components import (
    BasicQuAM,
    SingleChannel,
    InOutSingleChannel,
    pulses,
    StickyChannelAddon,
)


# Update the logging configuration
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("hpack.hpack").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

# %% Create config and connect to QM
machine = BasicQuAM()

machine.channels["ch1"] = SingleChannel(
    opx_output=("con1", 1), sticky=StickyChannelAddon(duration=10_000, digital=False)
)
machine.channels["ch2"] = SingleChannel(
    opx_output=("con1", 2), sticky=StickyChannelAddon(duration=10_000, digital=False)
)
readout_pulse = pulses.SquareReadoutPulse(id="readout", length=1000, amplitude=0.1)
machine.channels["ch_readout"] = InOutSingleChannel(
    opx_output=("con1", 3),
    opx_input=("con1", 1),
    intermediate_frequency=100e6,
    operations={"readout": readout_pulse},
)

# %% Open communication to the OPX 
# qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qmm = QuantumMachinesManager(host="192.168.8.4", cluster_name="Cluster_1")

# %% Set the scan mode and its acquisition parameters (more can be added to the GUI)
x_offset = VoltageParameter(name="X Voltage Offset", initial_value=0.0)
y_offset = VoltageParameter(name="Y Voltage Offset", initial_value=0.0)
inner_loop_action = BasicInnerLoopActionQuam(
    x_element=machine.channels["ch1"],
    y_element=machine.channels["ch2"],
    readout_pulse=readout_pulse,
    ramp_rate=3000,
)

scan_mode = scan_modes.RasterScan()

data_acquirer = OPXQuamDataAcquirer(
    qmm=qmm,
    machine=machine,
    qua_inner_loop_action=inner_loop_action,
    scan_mode=scan_mode,
    x_axis=SweepAxis("x", span=0.03, points=11, offset_parameter=x_offset),
    y_axis=SweepAxis("y", span=0.03, points=6, offset_parameter=y_offset),
    result_type="amplitude",
)

# %% Simulate or execute
simulate = False
if simulate:
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
else:

    # %% Run program and acquire data
    data_acquirer.run_program()
    # results = data_acquirer.acquire_data()
    # print(f"Mean of results: {np.mean(np.abs(results))}")
    # %% Run Video Mode
    live_plotter = VideoMode(data_acquirer=data_acquirer, update_interval=0.05)
    live_plotter.run(use_reloader=False)

    # QDAC control
    from qualang_tools.control_panel.voltage_control.voltage_parameters import QDACII, qdac_ch
    from qualang_tools.control_panel.voltage_control.main import start_voltage_control

    qdac = QDACII("ethernet", IP_address="192.168.8.17", port=5025)
    # Create dummy parameters
    parameters = [qdac_ch(qdac, idx, f"V{idx}", initial_value=0) for idx in range(1, 5)]
    for parameter in parameters:
        parameter.get()
    start_voltage_control(parameters=parameters, mini=True, use_thread=False)

# %% DEBUG: Generate QUA script
# from qm import generate_qua_script
#
# qua_script = generate_qua_script(data_acquirer.generate_program(), config)
# print(qua_script)
