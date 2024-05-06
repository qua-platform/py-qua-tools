import abc


class TimelineBase:
    def __init__(self, qubit_index: int):
        self.qubit_index: int = qubit_index
        self._current_time: float = 0
        self._current_phase: float = 0.

    @abc.abstractmethod
    def is_passive(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def is_empty(self):
        raise NotImplementedError()
