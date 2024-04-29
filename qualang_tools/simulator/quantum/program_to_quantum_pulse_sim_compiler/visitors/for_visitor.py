from qualang_tools.simulator.quantum.program_ast.program_for import For
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.expressions.expression_visitor import \
    ExpressionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class ForVisitor(Visitor):
    def visit(self, node: For, context: Context):
        condition = ExpressionVisitor().visit(node.cond, context)

        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.node_visitor import \
            NodeVisitor
        node_visitor = NodeVisitor()
        while condition:
            for inner_node in node.body:
                inner_node.accept(node_visitor, context)
            condition = ExpressionVisitor().visit(node.cond, context)
