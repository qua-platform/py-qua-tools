# from qiskit import pulse
# from qiskit.pulse.channels import PulseChannel
#
# from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.instruction import Instruction
# from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.instruction_visitor import \
#     InstructionVisitor
# from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.visitor import Visitor
#
#
# class SimultaneousVisitor(Visitor):
#     def visit(self, instruction: 'Simultaneous', pulse_channel: PulseChannel):
#         instruction_visitor = InstructionVisitor()
#         for simultaneous_instruction in instruction.instructions:
#             with pulse.align_right():
#                 simultaneous_instruction.accept(instruction_visitor, pulse_channel=pulse_channel)
