from typing import List

from qiskit.pulse import Schedule
from qiskit_dynamics import DynamicsBackend


class QuantumPulseSimulator:
    def __init__(self, backend: DynamicsBackend, schedules: List):
        self.backend = backend
        self.schedules: List[Schedule] = schedules

    def plot_schedule(self, index: int):
        from qiskit.visualization import pulse_drawer_v2

        pulse_drawer_v2(
            program=self.schedules[index],
            style=None,
            backend=None,
            time_range=None,
            time_unit="ns",
            disable_channels=None,
            show_snapshot=True,
            show_framechange=True,
            show_waveform_info=True,
            show_barrier=True,
            plotter="mpl2d",
            axis=None,
        )

    def run(self, num_shots: int) -> List[List[float]]:
        job = self.backend.run(self.schedules, shots=num_shots)
        result = job.result()

        results = []
        for i in range(len(self.schedules)):
            counts = result.get_counts(i)
            num_measured_qubits = len(list(counts.keys())[0])
            if num_measured_qubits == 1:
                results.append((
                    counts.get('0', 0) / num_shots,
                ))
            elif num_measured_qubits == 2:
                results.append((
                    # 1 - zero population is better for reproducing leakage induced
                    # readout errors assuming '2' is a valid state
                    1 - (counts.get('10', 0) / num_shots + counts.get('00', 0) / num_shots),
                    1 - (counts.get('01', 0) / num_shots + counts.get('00', 0) / num_shots),
                ))
            else:
                raise NotImplementedError(f"{num_measured_qubits} not supported yet.")

        return list(zip(*results))
