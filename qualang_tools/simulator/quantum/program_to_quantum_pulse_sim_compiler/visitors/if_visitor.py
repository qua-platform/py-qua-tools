from qualang_tools.simulator.quantum.program_ast._if import If
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.expression_visitors.expression_visitor import \
    ExpressionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class IfVisitor(Visitor):
    def visit(self, node: If, context: Context):
        condition = ExpressionVisitor().visit(node.cond, context)

        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.node_visitor import \
            NodeVisitor
        node_visitor = NodeVisitor()
        if condition:
            for inner_node in node.body:
                inner_node.accept(node_visitor, context)
