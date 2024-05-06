import abc


class TimelineBuilder(abc.ABC):
    @abc.abstractmethod
    def reset_phase(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def delay(self, duration: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def phase_offset(self, phase: float):
        raise NotImplementedError()
