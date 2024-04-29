from typing import List

from qiskit_dynamics import DynamicsBackend


class QuantumPulseSimulator:
    def __init__(self, backend: DynamicsBackend, schedules: List):
        self.backend = backend
        self.schedules = schedules

    def run(self, num_shots=1):
        job = self.backend.run(self.schedules, shots=num_shots)
        result = job.result()

        results = []
        for i in range(len(self.schedules)):
            results.append(result.get_counts(i).get('1', 0) / num_shots)

        return results