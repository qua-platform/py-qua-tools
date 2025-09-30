import abc
from typing import Tuple, Generator, Optional

from qm.jobs.running_qm_job import RunningQmJob
from typing import List


class Sequencer(abc.ABC):
    def __init__(self, rb: 'TwoQubitRb'):
        self.rb = rb
        self.sequences: Optional[Generator[List[int]]] = None

    @abc.abstractmethod
    def initialize_qua_memory(self):
        """ Called in a QUA program to do initial setup of variables. """
        raise NotImplementedError()

    @abc.abstractmethod
    def increment_qua_sequence(self) -> Tuple[dict, int]:
        """
        Called in a QUA program to increment the QUA sequence.

        Returns:

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def update_sequence_async(self, job: RunningQmJob):
        """ An asynchronous call to feed the live QUA program with data. """
        raise NotImplementedError()
