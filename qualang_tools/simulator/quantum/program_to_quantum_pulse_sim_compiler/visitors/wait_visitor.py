from qualang_tools.simulator.quantum.program_ast.wait import Wait
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.expression_visitors.expression_visitor import \
    ExpressionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class WaitVisitor(Visitor):
    def visit(self, node: Wait, context: Context):
        time = ExpressionVisitor().visit(node.time, context)
        if isinstance(time, float):
            time = cast_within_tolerance(time)

        # convert into clock cycles from ns
        time *= 4

        if node.elements == []:
            for element in context.schedules.get_elements():
                timeline = context.schedules.get_timeline(element)
                timeline.delay(time)
        else:
            for element in node.elements:
                timeline = context.schedules.get_timeline(element)
                timeline.delay(time)


def cast_within_tolerance(value: float, epsilon=1e-5):
    if int(value) - epsilon <= value <= int(value) + epsilon:
        return int(value)
    else:
        raise ValueError("Value is not within the tolerance range.")
