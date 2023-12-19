import numpy as np
import pytest
from qualang_tools.loops import *
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig, LoopbackInterface
from copy import deepcopy
import matplotlib.pyplot as plt


@pytest.fixture
def config():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [
            float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]
        ]

    return {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.0}},
                "digital_outputs": {},
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            }
        },
        "elements": {
            "resonator": {
                "singleInput": {
                    "port": ("con1", 1),
                },
                "intermediate_frequency": 100e6,
                "operations": {
                    "readout": "readout_pulse",
                },
                "outputs": {
                    "out1": ("con1", 1),
                    "out2": ("con1", 2),
                },
                "time_of_flight": 24,
                "smearing": 0,
            },
        },
        "pulses": {
            "readout_pulse": {
                "operation": "measurement",
                "length": 80,
                "waveforms": {
                    "single": "const_wf",
                },
                "integration_weights": {
                    "cos": "cosine_weights",
                    "sin": "sine_weights",
                    "minus_sin": "minus_sine_weights",
                },
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "integration_weights": {
            "cosine_weights": {
                "cosine": [(1.0, 80)],
                "sine": [(0.0, 80)],
            },
            "sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(1.0, 80)],
            },
            "minus_sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(-1.0, 80)],
            },
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 0,
                    "lo_frequency": 0,
                    "correction": IQ_imbalance(0.0, 0.0),
                }
            ],
        },
    }


def simulate_program_and_return(config, prog, duration=50000):
    qmm = QuantumMachinesManager()
    # qmm.close_all_quantum_machines()
    # job = qmm.simulate(
    #     config,
    #     prog,
    #     SimulationConfig(
    #         duration,
    #         simulation_interface=LoopbackInterface([("con1", 1, "con1", 1)]),
    #         include_analog_waveforms=True,
    #     ),
    # )

    qm = qmm.open_qm(config)
    job = qm.execute(prog)
    return job


def test_qua_arange(config):
    def prog_maker(arange_param):
        if float(arange_param[2]).is_integer():
            with program() as prog:
                a = declare(int)
                a_st = declare_stream()
                with for_(
                    *qua_arange(a, arange_param[0], arange_param[1], arange_param[2])
                ):
                    update_frequency("resonator", a)
                    play("readout", "resonator")
                    save(a, a_st)
                with stream_processing():
                    a_st.save_all("a")
            return prog
        else:
            with program() as prog:
                a = declare(fixed)
                a_st = declare_stream()
                with for_(
                    *qua_arange(a, arange_param[0], arange_param[1], arange_param[2])
                ):
                    play("readout" * amp(a), "resonator")
                    save(a, a_st)
                with stream_processing():
                    a_st.save_all("a")
            return prog

    cfg = deepcopy(config)

    arange_param_list = [
        [-0.05, -1, -0.15],
        [10, 20, 1],
        [20, 71, 2],
        [20, 71, 1],
        [11, 0, -1],
        [-11, -100, -2],
        [0.1, 1, 0.2],
        [0, 1, 0.2],
        [0, 2, 0.0001],
        [-1, 2, 0.00011],
        [-1, 1, 0.2],
        [0.00015, 1, 0.0001],
        [0, -2, -0.001],
        # [-1, 2, 0.00006],
    ]

    for param in arange_param_list:
        print(f"Test qua_arange with {param}:")
        job = simulate_program_and_return(cfg, prog_maker(param))
        job.result_handles.wait_for_all_values()
        a_qua = job.result_handles.get("a").fetch_all()["value"]
        a_list = np.arange(param[0], param[1], param[2])
        assert len(a_list) == len(a_qua)
        assert np.allclose(a_list, a_qua, atol=1e-4)


def test_from_array(config):
    def prog_maker(list_param):
        if list_param[1] == "int":
            with program() as prog:
                a = declare(int)
                a_st = declare_stream()
                with for_(*from_array(a, list_param[0])):
                    update_frequency("resonator", a)
                    play("readout", "resonator")
                    save(a, a_st)
                with stream_processing():
                    a_st.save_all("a")
            return prog
        else:
            with program() as prog:
                a = declare(fixed)
                a_st = declare_stream()
                with for_(*from_array(a, list_param[0])):
                    play("readout" * amp(a), "resonator")
                    save(a, a_st)
                with stream_processing():
                    a_st.save_all("a")
            return prog

    cfg = deepcopy(config)
    arange_param_list = [
        [np.logspace(np.log10(4), np.log10(10000), 29), "int"],
        [np.logspace(np.log10(50), np.log10(12500), 19), "int"],
        [np.logspace(np.log10(50000), np.log10(33), 72), "int"],
        [np.logspace(6, 4, 19), "int"],
        [np.logspace(3, 6, 199), "int"],
        [np.logspace(-3, 0, 99), "fixed"],
        [np.logspace(-3.5, -1, 11), "fixed"],
        [np.logspace(0.5, -0.5, 22), "fixed"],
        [np.logspace(0.5, -3.5, 21), "fixed"],
        [np.arange(-7.0547, -2.2141, 0.1015), "fixed"],
        [np.arange(-0.05, -1, -0.15), "fixed"],
        [np.arange(-1, 2, 0.0006), "fixed"],
        [np.arange(-11, -100, -2), "int"],
        [np.arange(20, 71, 2), "int"],
        [np.linspace(20, 71, 52), "int"],
        [np.linspace(0.1, 1, 6), "fixed"],
        [np.arange(10, 20, 1), "int"],
        [np.arange(20, 71, 1), "int"],
        [np.arange(0, 71, 2), "int"],
        [np.arange(0, 1, 0.1), "fixed"],
        [np.arange(0, 1, 0.2), "fixed"],
        [np.arange(0.1, 1, 0.2), "fixed"],
        # [np.arange(0.00015, 1, 0.0001), "fixed"],
    ]

    for param in arange_param_list:
        print(f"Test qua_list with {param}:")
        job = simulate_program_and_return(cfg, prog_maker(param))
        job.result_handles.wait_for_all_values()
        a_qua = job.result_handles.get("a").fetch_all()["value"]
        a_list = param[0]

        if (param[1] == "int") and (
            np.isclose(a_list[1] / a_list[0], a_list[-1] / a_list[-2])
        ):
            a_list = get_equivalent_log_array(a_list)

        assert len(a_list) == len(a_qua)
        assert np.allclose(a_list, a_qua, atol=1e-4)
    print("PASSED !")


def test_qua_linspace(config):
    def prog_maker(linspace_param):
        with program() as prog:
            a = declare(fixed)
            a_st = declare_stream()
            with for_(
                *qua_linspace(
                    a, linspace_param[0], linspace_param[1], linspace_param[2]
                )
            ):
                play("readout" * amp(a), "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")
        return prog

    cfg = deepcopy(config)

    arange_param_list = [
        [0.1, 1, 5],
        [0.1, 0.95, 5],
        [-1, 0, 2],
        [-1, 1, 2],
        [-8, 7, 51],
        [-0.1, 0.1, 5000],
        [-1, 2, 11],
    ]

    for param in arange_param_list:
        print(f"Test qua_arange with {param}:")
        job = simulate_program_and_return(cfg, prog_maker(param))
        job.result_handles.wait_for_all_values()
        a_qua = job.result_handles.get("a").fetch_all()["value"]
        a_list = np.linspace(param[0], param[1], param[2])
        print(a_list)
        print(a_qua)
        print(a_list - a_qua)
        assert len(a_list) == len(a_qua)
        assert np.allclose(a_list, a_qua, atol=1e-4)


def test_qua_logspace_fixed(config):
    def prog_maker(logspace_param):
        with program() as prog:
            a = declare(fixed)
            a_st = declare_stream()
            with for_(
                *qua_logspace(
                    a, logspace_param[0], logspace_param[1], logspace_param[2]
                )
            ):
                play("readout" * amp(a), "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")
        return prog

    cfg = deepcopy(config)

    arange_param_list = [
        [0.5, -2, 24],
        [0, -3, 51],
        [0, -3, 50],
        [-4, 0.5, 11],
        [-3.8, 0.2, 7],
    ]
    for param in arange_param_list:
        print(f"Test qua_logspace with {param}:")
        job = simulate_program_and_return(cfg, prog_maker(param))
        job.result_handles.wait_for_all_values()
        a_qua = job.result_handles.get("a").fetch_all()["value"]
        a_list = np.logspace(param[0], param[1], param[2])
        assert len(a_list) == len(a_qua)
        assert np.allclose(a_list, a_qua, atol=1e-4)


def test_qua_logspace_int(config):
    def prog_maker(logspace_param):
        with program() as prog:
            t = declare(int)
            t_st = declare_stream()
            with for_(
                *qua_logspace(
                    t, logspace_param[0], logspace_param[1], logspace_param[2]
                )
            ):
                play("readout", "resonator", duration=t)
                save(t, t_st)
            with stream_processing():
                t_st.save_all("a")
        return prog

    cfg = deepcopy(config)

    arange_param_list = [
        [np.log10(500), np.log10(12500), 11],
        [np.log10(5000), np.log10(125), 30],
        [np.log10(40), np.log10(1001), 51],
    ]
    for param in arange_param_list:
        print(f"Test qua_logspace with {param}:")
        job = simulate_program_and_return(cfg, prog_maker(param))
        job.result_handles.wait_for_all_values()
        a_qua = job.result_handles.get("a").fetch_all()["value"]
        a_list = get_equivalent_log_array(
            np.round(np.logspace(param[0], param[1], param[2]))
        )
        assert len(a_list) == len(a_qua)
        assert np.allclose(a_list, a_qua, atol=1e-4)
