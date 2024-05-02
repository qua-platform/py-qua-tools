import numpy as np
from matplotlib import pyplot as plt
from qm.qua import *

from qualang_tools.simulator.quantum.simulate import simulate


def test_rabi(transmon_pair_backend, transmon_pair_qua_config, config_to_transmon_pair_backend_map):
    start, stop, step = -2, 2, 0.1
    with program() as prog:
        a = declare(fixed)

        with for_(a, start, a < stop - 0.0001, a + step):
            play("x90"*amp(a), "qubit_1")
            play("x90"*amp(a), "qubit_2")

            align("qubit_1", "qubit_2", "resonator_1", "resonator_2")
            measure("readout", "resonator_1", None)
            measure("readout", "resonator_2", None)

    results = simulate(
        qua_program=prog,
        qua_config=transmon_pair_qua_config,
        qua_config_to_backend_map=config_to_transmon_pair_backend_map,
        backend=transmon_pair_backend,
        num_shots=10_000
    )

    for i, result in enumerate(results):
        plt.plot(np.arange(start, stop, step), results[i], label=f"Q{i}")
        plt.ylim(-0.05, 1.05)
    plt.legend()
    plt.show()


# def test_ramsey(transmon_backend, config):
#     start, stop, step = 10, 800, 20
#     with program() as prog:
#         t = declare(fixed)
#
#         with for_(t, start, t < stop, t + step):
#             play("x90"*amp(-1.12), "qubit")
#             wait(t, "qubit")
#             play("x90"*amp(-1.12), "qubit")
#
#             align("qubit", "resonator")
#             measure("readout", "resonator", None)
#
#     print(transmon_backend)
#     sim = Compiler(config=config).compile(prog, transmon_backend)
#     results = sim.run(num_shots=10_000)
#
#     plt.plot(np.arange(start, stop, step), results)
#     plt.ylim(-0.05, 1.05)
#     plt.show()
