import numpy as np
from qiskit import pulse

from qualang_tools.simulator.quantum.program_ast.play import Play
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import get_timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.expression_visitors.expression_visitor import \
    ExpressionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.pulses import \
    lookup_pulse_parameters
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class PlayVisitor(Visitor):
    def visit(self, node: Play, context: Context):
        e = node.element

        length, I, Q = lookup_pulse_parameters(node, context.qua_config)

        if node.duration is not None:
            length = ExpressionVisitor().visit(node.duration, context)

        if node.amp is not None:
            I *= ExpressionVisitor().visit(node.amp, context)
            Q *= ExpressionVisitor().visit(node.amp, context)

        I_shape = pulse.library.Constant(length, I)
        Q_shape = pulse.library.Constant(length, Q)

        timeline = get_timeline(e, context.timelines)

        # fixme: currently simultaneous (align_left) can't be nested in
        #  a timeline (align_sequential)
        # s = timeline.simultaneous()
        # s.play(length, I_shape)
        # s.play(length, Q_shape, phase=np.pi/2)

        timeline.play(length, I_shape)
        timeline.play(length, Q_shape, phase=np.pi/2)
