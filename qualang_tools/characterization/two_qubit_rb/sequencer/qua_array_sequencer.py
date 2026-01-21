from typing import Tuple

from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import declare, switch_, case_, for_, assign

from qualang_tools.characterization.two_qubit_rb.sequencer.sequencer import Sequencer


class QuaArraySequencer(Sequencer):
    def initialize_qua_memory(self):
        """ Called in a QUA program to do initial setup of variables. """
        if self.sequences is None:
            raise ValueError('The `sequences` attribute must be set in advance.')

        self.sequence_index = declare(int, value=0)
        self.lengths, self.gates = [], []
        for sequence in self.sequences:
            if self.rb._sequence_tracker is not None:
                self.rb._sequence_tracker.make_sequence(sequence)
            self.gates.append({
                qe: declare(int, value=self.rb._decode_sequence_for_element(qe, sequence))
                for qe in self.rb._rb_baker.all_elements
            })
            self.lengths.append(declare(int, value=len(sequence)))

        self.current_sequence_length = declare(int)
        self.current_sequence = {
            qe: declare(int, size=self.rb._buffer_length)
            for qe in self.rb._rb_baker.all_elements
        }

    def increment_qua_sequence(self) -> Tuple[dict, int]:
        """ Called in a QUA program to increment the QUA sequence. """
        j = declare(int, value=0)
        with switch_(self.sequence_index):
            for qe in self.rb._rb_baker.all_elements:
                for i, sequence in enumerate(self.sequences):
                    with case_(i):
                        length = self.lengths[i]
                        with for_(j, 0, j < length, j + 1):
                            assign(self.current_sequence[qe][j], self.gates[i][qe][j])

        assign(self.sequence_index, self.sequence_index + 1)

        return self.current_sequence, self.current_sequence_length

    def update_sequence_async(self, job: RunningQmJob):
        pass
