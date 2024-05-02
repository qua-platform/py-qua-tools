from qiskit import pulse
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.instruction import Instruction
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.instruction_visitor import \
    InstructionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class SimultaneousVisitor(Visitor):
    def visit(self, instruction: 'Simultaneous', drive_channel: int):
        instruction_visitor = InstructionVisitor()
        for simultaneous_instruction in instruction.instructions:
            with pulse.align_left():
                simultaneous_instruction.accept(instruction_visitor, drive_channel=drive_channel)
