from qm.qua import *
from copy import deepcopy
from qm import QuantumMachinesManager
from qm import SimulationConfig
from qualang_tools.results import progress_counter, fetching_tool
from qualang_tools.plot import interrupt_on_close
from qualang_tools.loops import from_array
from qualang_tools.voltage_gates import VoltageGateSequence
import numpy as np
import pytest
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

@pytest.fixture
def config():
    readout_len = 2000
    # Reflectometry
    resonator_IF = 151 * 1e6
    reflectometry_readout_length = readout_len
    reflectometry_readout_amp = 0.03
    # Time of flight
    time_of_flight = 24
    # Step parameters
    step_length = 16
    P1_step_amp = 0.25
    P2_step_amp = 0.25
    charge_sensor_amp = 0.25
    # Time to ramp down to zero for sticky elements in ns
    hold_offset_duration = 4

    config = {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0},  # P1
                    2: {"offset": 0.0},  # P2
                    3: {"offset": 0.0},  # Sensor gate
                    9: {"offset": 0.0},  # RF reflectometry
                    10: {"offset": 0.0},  # DC readout
                },
                "digital_outputs": {
                    1: {},  # TTL for QDAC
                    2: {},  # TTL for QDAC
                },
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # RF reflectometry input
                    2: {"offset": 0.0, "gain_db": 0},  # DC readout input
                },
            },
        },
        "elements": {
            "P1": {
                "singleInput": {
                    "port": ("con1", 1),
                },
                "operations": {
                    "step": "P1_step_pulse",
                },
            },
            "P1_sticky": {
                "singleInput": {
                    "port": ("con1", 1),
                },
                "sticky": {"analog": True, "duration": hold_offset_duration},
                "operations": {
                    "step": "P1_step_pulse",
                },
            },
            "P2": {
                "singleInput": {
                    "port": ("con1", 2),
                },
                "operations": {
                    "step": "P2_step_pulse",
                },
            },
            "P2_sticky": {
                "singleInput": {
                    "port": ("con1", 2),
                },
                "sticky": {"analog": True, "duration": hold_offset_duration},
                "operations": {
                    "step": "P2_step_pulse",
                },
            },
            "sensor_gate": {
                "singleInput": {
                    "port": ("con1", 3),
                },
                "operations": {
                    "step": "bias_charge_pulse",
                },
            },
            "sensor_gate_sticky": {
                "singleInput": {
                    "port": ("con1", 3),
                },
                "sticky": {"analog": True, "duration": hold_offset_duration},
                "operations": {
                    "step": "bias_charge_pulse",
                },
            },
            "qdac_trigger1": {
                "digitalInputs": {
                    "trigger": {
                        "port": ("con1", 1),
                        "delay": 0,
                        "buffer": 0,
                    }
                },
                "operations": {
                    "trigger": "trigger_pulse",
                },
            },
            "qdac_trigger2": {
                "digitalInputs": {
                    "trigger": {
                        "port": ("con1", 2),
                        "delay": 0,
                        "buffer": 0,
                    }
                },
                "operations": {
                    "trigger": "trigger_pulse",
                },
            },
            "tank_circuit": {
                "singleInput": {
                    "port": ("con1", 9),
                },
                "intermediate_frequency": resonator_IF,
                "operations": {
                    "readout": "reflectometry_readout_pulse",
                },
                "outputs": {
                    "out1": ("con1", 1),
                    "out2": ("con1", 2),
                },
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
        },
        "pulses": {
            "P1_step_pulse": {
                "operation": "control",
                "length": step_length,
                "waveforms": {
                    "single": "P1_step_wf",
                },
            },
            "P2_step_pulse": {
                "operation": "control",
                "length": step_length,
                "waveforms": {
                    "single": "P2_step_wf",
                },
            },
            "bias_charge_pulse": {
                "operation": "control",
                "length": step_length,
                "waveforms": {
                    "single": "charge_sensor_step_wf",
                },
            },
            "trigger_pulse": {
                "operation": "control",
                "length": 1000,
                "digital_marker": "ON",
            },
            "reflectometry_readout_pulse": {
                "operation": "measurement",
                "length": reflectometry_readout_length,
                "waveforms": {
                    "single": "reflect_wf",
                },
                "integration_weights": {
                    "cos": "cosine_weights",
                    "sin": "sine_weights",
                },
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "P1_step_wf": {"type": "constant", "sample": P1_step_amp},
            "P2_step_wf": {"type": "constant", "sample": P2_step_amp},
            "charge_sensor_step_wf": {"type": "constant", "sample": charge_sensor_amp},
            "reflect_wf": {"type": "constant", "sample": reflectometry_readout_amp},
            "zero_wf": {"type": "constant", "sample": 0.0},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "integration_weights": {
            "constant_weights": {
                "cosine": [(1, readout_len)],
                "sine": [(0.0, readout_len)],
            },
            "cosine_weights": {
                "cosine": [(1.0, reflectometry_readout_length)],
                "sine": [(0.0, reflectometry_readout_length)],
            },
            "sine_weights": {
                "cosine": [(0.0, reflectometry_readout_length)],
                "sine": [(1.0, reflectometry_readout_length)],
            },
        },
    }
    return config

def get_filtered_voltage(
    voltage_list, step_duration: float, bias_tee_cut_off_frequency: float, plot: bool = False
):
    """Get the voltage after filtering through the bias-tee

    :param voltage_list: List of voltages outputted by the OPX in V.
    :param step_duration: Duration of each step in s.
    :param bias_tee_cut_off_frequency: Cut-off frequency of the bias-tee in Hz.
    :param plot: Flag to plot the voltage values if set to True.
    :return: the filtered and unfiltered voltage lists with 1Gs/s sampling rate.
    """

    def high_pass(data, f_cutoff):
        res = butter(1, f_cutoff, btype="high", analog=False)
        return lfilter(res[0], res[1], data)

    y = [val for val in voltage_list for _ in range(int(step_duration * 1e9))]
    y_filtered = high_pass(y, bias_tee_cut_off_frequency * 1e-9)
    if plot:
        plt.plot(y, label="before bias-tee")
        plt.plot(y_filtered, label="after bias-tee")
        plt.xlabel("Time [ns]")
        plt.ylabel("Voltage [V]")
        plt.legend()
    print(f"Error: {np.mean(np.abs((y-y_filtered)/(max(y)-min(y))))*100:.2f} %")
    return y, y_filtered


def simulate_program_and_return(config, prog, simulation_duration=100_000):
    qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
    simulation_config = SimulationConfig(duration=simulation_duration // 4)
    job = qmm.simulate(config, prog, simulation_config)
    return job

###################
# The QUA program #
###################
@pytest.mark.parametrize(
    ["t_R", "t", "compensation_amp", "slew_rate", "cut_off"],
    [
        [16, 0, 0.25, None, 10000],
        [16, 16, 0.01, None, 10000],
        [16, 16, 0.49, None, 10000],
        [1000, 2000, 0.5, None, 6000],
    ],
)
def test_all_python(config, t_R, t, compensation_amp, slew_rate, cut_off):
    def prog_maker(_t_R, _t, _compensation_amp, _slew_rate):
        with program() as prog:
            n = declare(int)
            with for_(n, 0, n < 100, n + 1):
                seq.add_step(voltage_point_name="initialization")
                seq.add_step(voltage_point_name="idle", ramp_duration=t_R, duration=t)
                seq.add_step(voltage_point_name="readout", ramp_duration=t_R, duration=t)
                seq.add_compensation_pulse(max_amplitude=_compensation_amp, slew_rate=_slew_rate)
                seq.ramp_to_zero()
        return prog

    cfg = deepcopy(config)
    seq = VoltageGateSequence(cfg, ["P1_sticky", "P2_sticky"])
    seq.add_points("initialization", [0.1, -0.1], 100)
    seq.add_points("idle", [0.2, -0.2], 100)
    seq.add_points("readout", [0.1, -0.1], 2000)
    job = simulate_program_and_return(cfg, prog_maker(t_R, t, compensation_amp, slew_rate))
    plt.figure()
    plt.subplot(211)
    job.get_simulated_samples().con1.plot()
    plt.subplot(212)
    y, y_filtered = get_filtered_voltage(job.get_simulated_samples().con1.analog["1"], 1e-9, cut_off, True)
    error = np.mean(np.abs((y - y_filtered) / (max(y) - min(y)))) * 100
    print(f"Error: {error:.2f} %")
    assert error < 2


@pytest.mark.parametrize(
    ["ramp_duration", "durations", "compensation_amp", "slew_rate", "cut_off"],
    [
        [16, np.arange(16, 200, 4), 0.5, None, 10000],
        [16, np.arange(16, 200, 4), 0.05, None, 10000],
        [1000, np.arange(16, 200, 4), 0.5, None, 10000],
        [1000, np.arange(16, 200, 4), 0.05, None, 10000],
    ],
)
def test_ramp_python_plateau_qua(config, ramp_duration, durations, compensation_amp, slew_rate, cut_off):
    def prog_maker(_ramp_duration, _durations, _compensation_amp, _slew_rate):
        with program() as prog:
            n = declare(int)
            t = declare(int)
            with for_(n, 0, n < 100, n + 1):
                with for_(*from_array(t, _durations)):
                    seq.add_step(voltage_point_name="initialization")
                    seq.add_step(voltage_point_name="idle", ramp_duration=_ramp_duration, duration=t)
                    seq.add_step(voltage_point_name="readout", ramp_duration=_ramp_duration, duration=t)
                    seq.add_compensation_pulse(max_amplitude=_compensation_amp, slew_rate=_slew_rate)
                    seq.ramp_to_zero()
        return prog

    cfg = deepcopy(config)
    seq = VoltageGateSequence(cfg, ["P1_sticky", "P2_sticky"])
    seq.add_points("initialization", [0.1, -0.1], 100)
    seq.add_points("idle", [0.2, -0.2], 100)
    seq.add_points("readout", [0.1, -0.1], 2000)
    job = simulate_program_and_return(cfg, prog_maker(ramp_duration, durations, compensation_amp, slew_rate))
    plt.figure()
    plt.subplot(211)
    job.get_simulated_samples().con1.plot()
    plt.subplot(212)
    y, y_filtered = get_filtered_voltage(job.get_simulated_samples().con1.analog["1"], 1e-9, cut_off, True)
    error = np.mean(np.abs((y - y_filtered) / (max(y) - min(y)))) * 100
    print(f"Error: {error:.2f} %")
    assert error < 2


@pytest.mark.parametrize(
    ["ramp_durations", "durations", "compensation_amp", "slew_rate", "cut_off"],
    [
        [np.arange(16, 200, 4), np.arange(52, 200, 4), 0.5, None, 10000],
        [np.arange(16, 200, 4), np.arange(52, 200, 4), 0.05, None, 10000],
    ],
)
def test_ramp_qua_plateau_qua(config, ramp_durations, durations, compensation_amp, slew_rate, cut_off):
    def prog_maker(_ramp_durations, _durations, _compensation_amp, _slew_rate):
        with program() as prog:
            n = declare(int)
            t = declare(int)
            t_R = declare(int)
            with for_(n, 0, n < 100, n + 1):
                with for_(*from_array(t, _durations)):
                    with for_(*from_array(t_R, _ramp_durations)):
                        seq.add_step(voltage_point_name="initialization")
                        seq.add_step(voltage_point_name="idle", ramp_duration=t_R, duration=t)
                        seq.add_step(voltage_point_name="readout", ramp_duration=t_R, duration=t)
                        seq.add_compensation_pulse(max_amplitude=_compensation_amp, slew_rate=_slew_rate)
                        seq.ramp_to_zero()
        return prog

    cfg = deepcopy(config)
    seq = VoltageGateSequence(cfg, ["P1_sticky", "P2_sticky"])
    seq.add_points("initialization", [0.1, -0.1], 100)
    seq.add_points("idle", [0.2, -0.2], 100)
    seq.add_points("readout", [0.1, -0.1], 2000)
    job = simulate_program_and_return(cfg, prog_maker(ramp_durations, durations, compensation_amp, slew_rate))
    plt.figure()
    plt.subplot(211)
    job.get_simulated_samples().con1.plot()
    plt.subplot(212)
    y, y_filtered = get_filtered_voltage(job.get_simulated_samples().con1.analog["1"], 1e-9, cut_off, True)
    error = np.mean(np.abs((y - y_filtered) / (max(y) - min(y)))) * 100
    print(f"Error: {error:.2f} %")
    assert error < 2


# def test_ramp_python_plateau_qua(config, duration_init, t_R, t, compensation_amp):
#     def prog_maker(_duration_init, _t_R, _t, _compensation_amp):
#         seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])
#         seq.add_points("initialization", [0.1, -0.1], _duration_init)
#         seq.add_points("idle", [0.2, -0.2], 100)
#         seq.add_points("readout", [0.1, -0.1], 2000)
#         n_avg = 1000
#         # Pulse duration sweep in ns - must be larger than 4 clock cycles
#         durations = np.arange(52, 200, 4)
#         # Pulse amplitude sweep (as a pre-factor of the qubit pulse amplitude) - must be within [-2; 2)
#         ramp_durations = np.arange(16, 200, 4)
#         with program() as prog:
#             n = declare(int)
#             t = declare(int)
#             t_R = declare(int)
#             n_st = declare_stream()
#
#             with for_(n, 0, n < n_avg, n + 1):
#                 save(n, n_st)
#                 with for_(*from_array(t, durations)):
#                     with for_(*from_array(t_R, ramp_durations)):
#                         align()
#                         seq.add_step(voltage_point_name="initialization")
#                         seq.add_step(voltage_point_name="idle", ramp_duration=t_R, duration=t)
#                         seq.add_step(voltage_point_name="readout", ramp_duration=t_R)
#                         seq.add_compensation_pulse(max_amplitude=0.35, slew_rate=1e-3)
#
#                         # Measure the dot right after the qubit manipulation
#                         wait(_duration_init // 4 + 2 * (t_R >> 2) + (t >> 2), "tank_circuit")
#                         measure("readout", "tank_circuit", None)
#                         seq.ramp_to_zero()
#             return prog
#
#     cfg = deepcopy(config)
#     job = simulate_program_and_return(cfg, prog_maker(duration_init, t_R, t, compensation_amp))
#     plt.figure()
#     plt.subplot(211)
#     job.get_simulated_samples().con1.plot()
#     plt.subplot(212)
#     y, y_filtered = get_filtered_voltage(job.get_simulated_samples().con1.analog["1"], 1e-9, 10000, True)
#     error = np.mean(np.abs((y - y_filtered) / (max(y) - min(y)))) * 100
#     print(f"Error: {np.mean(np.abs((y - y_filtered) / (max(y) - min(y)))) * 100:.2f} %")
#     assert error < 2



