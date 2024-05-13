import time

import numpy as np
from qm import QuantumMachinesManager


class ResultStub:
    def __init__(self, value=0):
        self.value = value

    def get(self):
        return self.value

    def fetch_all(self):
        return self.value

    def wait_for_values(self, wait_time=0):
        time.sleep(wait_time)
        return True


class ResultHandlesStub:
    def __init__(self):
        self.n = ResultStub()
        self.I1 = ResultStub()
        self.Q1 = ResultStub()
        self.I2 = ResultStub()
        self.Q2 = ResultStub()
        self.I = ResultStub()
        self.Q = ResultStub()
        self.iteration = ResultStub()
        self.processing = True

    def is_processing(self):
        if self.processing:
            self.processing = False
            return True
        else:
            return False

    def get(self, attr):
        return getattr(self, attr)


class JobStub:
    def __init__(self):
        self.result_handles = ResultHandlesStub()
        self.processing = True

    def halt(self):
        pass

    def fetch_all(self):
        return 1, 1, 1


class QuantumMachineStub:
    def close(self):
        pass

    def execute(self, program) -> JobStub:
        return JobStub()


class QuantumMachinesManagerStub(QuantumMachinesManager):
    def __init__(self, **kwargs):
        pass

    def open_qm(self, config):
        return QuantumMachineStub()
