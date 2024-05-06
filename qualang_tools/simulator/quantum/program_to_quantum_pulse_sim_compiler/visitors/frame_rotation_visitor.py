import numpy as np

from qualang_tools.simulator.quantum.program_ast.frame_rotation_2pi import FrameRotation2Pi
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.expression_visitors.expression_visitor import \
    ExpressionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class FrameRotationVisitor(Visitor):
    def visit(self, node: FrameRotation2Pi, context: Context):
        phase = ExpressionVisitor().visit(node.phase, context)
        phase *= 2*np.pi

        for element in node.elements:
            timeline = context.schedules.get_timeline(element)
            timeline.phase_offset(phase)
