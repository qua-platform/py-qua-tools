from qiskit import pulse

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.delay import Delay
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.visitor import Visitor


class DelayVisitor(Visitor):
    def visit(self, instruction: Delay, instruction_context: Context):
        pulse.delay(instruction.duration, instruction_context.timeline.pulse_channel)
