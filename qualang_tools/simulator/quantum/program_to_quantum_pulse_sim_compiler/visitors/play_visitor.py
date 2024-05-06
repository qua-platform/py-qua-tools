from qualang_tools.simulator.quantum.program_ast.play import Play
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_IQ import TimelineIQ
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.expression_visitors.expression_visitor import \
    ExpressionVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.pulses import \
    waveform_shape
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor


class PlayVisitor(Visitor):
    def visit(self, node: Play, context: Context):
        e = node.element

        length = None
        if node.duration is not None:
            length = ExpressionVisitor().visit(node.duration, context)

        amp_scaling_factor = None
        if node.amp is not None:
            amp_scaling_factor = ExpressionVisitor().visit(node.amp, context)

        length, [I_shape, Q_shape] = waveform_shape(node, context.qua_config, length, amp_scaling_factor)

        timeline = context.schedules.get_timeline(e)

        if isinstance(timeline, TimelineIQ):
            timeline.play_i(length, I_shape)
            timeline.play_q(length, Q_shape)
        else:
            raise NotImplementedError()
