from qiskit import pulse
from qiskit.pulse import DriveChannel

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines import Instruction


class InstructionVisitor:
    def visit(self, instruction: Instruction, drive_channel: int):
        if instruction.type == 'play':
            shape = pulse.library.Constant(
                instruction.duration,
                **instruction.args
            )
            pulse.play(shape, DriveChannel(drive_channel))
        elif instruction.type == 'acquire':
            pulse.acquire(
                instruction.duration,
                drive_channel,
                pulse.MemorySlot(0)
            )

        elif instruction.type == 'delay':
            pulse.delay(instruction.duration, DriveChannel(drive_channel))

        else:
            raise NotImplementedError(f'Unrecognised instruction type {instruction.type}')