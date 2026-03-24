import numpy as np

from qm.qua.extensions.qua_iterators import QuaIterable, NativeIterable, QuaIterableRange, QuaProduct, NativeIterableRange
from qm import SimulationConfig, LoopbackInterface


simulation_config = SimulationConfig(50000, simulation_interface=LoopbackInterface([("con1", 2, 8, "con1", 2, 1)]))

shots = 100
frequencies = np.linspace(1, 2, 5)
amp_start = 1.1
amp_stop = 4
amp_step = 2
amp_values = np.arange(amp_start, amp_stop, amp_step)
qubits = ["q1", "q2", "q3"]


def make_product():
    return QuaProduct([
        QuaIterableRange("shot", shots),
        NativeIterable("qubit", qubits),
        QuaIterable("frequency", frequencies),
        NativeIterableRange("amp", amp_start, amp_stop, amp_step)
    ])
