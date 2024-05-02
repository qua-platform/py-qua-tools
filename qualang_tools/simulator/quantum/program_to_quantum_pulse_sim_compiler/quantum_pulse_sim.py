from typing import List

from qiskit_dynamics import DynamicsBackend


class QuantumPulseSimulator:
    def __init__(self, backend: DynamicsBackend, schedules: List):
        self.backend = backend
        self.schedules = schedules

    def run(self, num_shots: int) -> List[List[float]]:
        job = self.backend.run(self.schedules, shots=num_shots)
        result = job.result()

        results = []
        for i in range(len(self.schedules)):
            counts = result.get_counts(i)
            num_measured_qubits = len(list(counts.keys())[0])
            if num_measured_qubits == 1:
                results.append((
                    counts.get('1', 0) / num_shots,
                ))
            elif num_measured_qubits == 2:
                results.append((
                    counts.get('01', 0) / num_shots + counts.get('11', 0) / num_shots,
                    counts.get('10', 0) / num_shots + counts.get('11', 0) / num_shots,
                ))
            else:
                raise NotImplementedError(f"{num_measured_qubits} not supported yet.")

        return list(zip(*results))
