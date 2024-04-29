import numpy as np
from matplotlib import pyplot as plt
from qm.qua import *

from qualang_tools.simulator.quantum import Compiler


def test_rabi(transmon_backend, config):
    start, stop, step = -2, 2, 0.1
    with program() as prog:
        a = declare(fixed)

        with for_(a, start, a < stop, a + step):
            play("x90"*amp(a), "qubit")

            align("qubit", "resonator")
            measure("readout", "resonator", None)

    sim = Compiler(config=config).compile(prog, transmon_backend)
    results = sim.run(num_shots=10_000)

    plt.plot(np.arange(start, stop, step), results)
    plt.ylim(-0.05, 1.05)
    plt.show()


def test_ramsey(transmon_backend, config):
    start, stop, step = 10, 800, 20
    with program() as prog:
        t = declare(fixed)

        with for_(t, start, t < stop, t + step):
            play("x90"*amp(-1.12), "qubit")
            wait(t, "qubit")
            play("x90"*amp(-1.12), "qubit")

            align("qubit", "resonator")
            measure("readout", "resonator", None)

    print(transmon_backend)
    sim = Compiler(config=config).compile(prog, transmon_backend)
    results = sim.run(num_shots=10_000)

    plt.plot(np.arange(start, stop, step), results)
    plt.ylim(-0.05, 1.05)
    plt.show()

