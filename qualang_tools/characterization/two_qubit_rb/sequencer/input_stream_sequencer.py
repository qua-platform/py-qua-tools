from typing import Tuple, Optional, Callable, List, Generator

from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import declare_input_stream, advance_input_stream, assign, declare

from qualang_tools.characterization.two_qubit_rb.sequencer.sequencer import Sequencer
from qualang_tools.characterization.two_qubit_rb.util import run_in_thread


def input_stream_name(element: str) -> str:
    return element.replace(".", "__dot__")


def random_sequence_generator(rb, num_circuits_per_depth, circuit_depths):
    for _ in range(num_circuits_per_depth):
        for circuit_depth in circuit_depths:
            yield rb._gen_rb_sequence(circuit_depth)


class InputStreamSequencer(Sequencer):
    def initialize_qua_memory(self):
        """ Called in a QUA program to do initial setup of variables. """
        self.gates_len_is = declare_input_stream(int, name="__gates_len_is__", size=1)
        self.gates_is = {
            qe: declare_input_stream(int, name=f"{input_stream_name(qe)}_is", size=self.rb._buffer_length)
            for qe in self.rb._rb_baker.all_elements
        }

    def increment_qua_sequence(self) -> Tuple[dict, int]:
        """ Called in a QUA program to increment the QUA sequence. """
        length = declare(int)
        advance_input_stream(self.gates_len_is)
        for gate_is in self.gates_is.values():
            advance_input_stream(gate_is)
        assign(length, self.gates_len_is[0])

        return self.gates_is, length

    @run_in_thread
    def update_sequence_async(self, job: RunningQmJob):
        """ An asynchronous call to feed the QUA program with data. """
        if self.sequences is None:
            raise ValueError('The `sequences` attribute must be set in advance.')
        for sequence in self.sequences:
            if self.rb._sequence_tracker is not None:
                self.rb._sequence_tracker.make_sequence(sequence)
            job.insert_input_stream("__gates_len_is__", len(sequence))
            for qe in self.rb._rb_baker.all_elements:
                job.insert_input_stream(
                    f"{input_stream_name(qe)}_is", self.rb._decode_sequence_for_element(qe, sequence)
                )
