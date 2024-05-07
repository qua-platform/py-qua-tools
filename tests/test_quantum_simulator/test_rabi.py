import numpy as np
from matplotlib import pyplot as plt
from qm.qua import *

from qualang_tools.simulator.quantum.simulate import simulate_program


def test_simultaneous_rabi(transmon_pair_backend, transmon_pair_qua_config, config_to_transmon_pair_backend_map):
    start, stop, step = -2, 2, 0.1
    with program() as prog:
        a = declare(fixed)

        with for_(a, start, a < stop - 0.0001, a + step):
            play("x90"*amp(a), "qubit_1")
            play("x90"*amp(a), "qubit_2")

            align("qubit_1", "qubit_2", "resonator_1", "resonator_2")
            measure("readout", "resonator_1", None)
            measure("readout", "resonator_2", None)

    results = simulate_program(
        qua_program=prog,
        qua_config=transmon_pair_qua_config,
        qua_config_to_backend_map=config_to_transmon_pair_backend_map,
        backend=transmon_pair_backend,
        num_shots=10_000,
    )
    # plt.show()

    # make sure no single point is different to expected within 0.1 tolerance
    q1_state_probabilities = np.array(results[0])
    q2_state_probabilities = np.array(results[0])
    amps = np.arange(start, stop, step)
    expected_state_probabilities = np.sin(np.pi*amps/4) ** 2
    assert np.allclose(q1_state_probabilities, expected_state_probabilities, atol=0.1)
    assert np.allclose(q2_state_probabilities, expected_state_probabilities, atol=0.1)

    # for i, result in enumerate(results):
    #     plt.plot(np.arange(start, stop, step), results[i], '.-', label=f"Simulated Q{i}")
    #     plt.ylim(-0.05, 1.05)
    # plt.plot(np.arange(start, stop, step), expected_state_probabilities, '.-', label=f"Expected")
    # plt.legend()
    # plt.show()
