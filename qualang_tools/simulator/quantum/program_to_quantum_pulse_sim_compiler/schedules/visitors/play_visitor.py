from qiskit import pulse

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.play import Play
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.visitor import Visitor


class PlayVisitor(Visitor):
    def visit(self, instruction: Play, instruction_context: Context):
        if instruction.phase == 0.:
            pulse.play(instruction.shape, instruction_context.timeline.pulse_channel, name=instruction.name)
        else:
            with pulse.phase_offset(instruction.phase, instruction_context.timeline.pulse_channel):
                pulse.play(instruction.shape, instruction_context.timeline.pulse_channel, name=instruction.name)
