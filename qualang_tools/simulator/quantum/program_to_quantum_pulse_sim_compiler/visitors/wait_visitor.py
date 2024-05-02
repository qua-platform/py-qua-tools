from qualang_tools.simulator.quantum.program_ast.wait import Wait
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import get_timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.expressions.expression_visitor import \
    ExpressionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class WaitVisitor(Visitor):
    def visit(self, node: Wait, context: Context):
        time = ExpressionVisitor().visit(node.time, context)

        if node.elements == []:
            for element in context.timelines:
                timeline = get_timeline(element, context.timelines)
                timeline.add_instruction('delay', time)
        else:
            for e in node.elements:
                timeline = get_timeline(e, context.timelines)
                timeline.add_instruction('delay', time)
