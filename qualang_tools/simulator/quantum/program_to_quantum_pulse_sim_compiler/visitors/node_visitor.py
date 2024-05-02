from qualang_tools.simulator.quantum.program_ast.node import Node
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.visitors.visitor import Visitor
from .align_visitor import AlignVisitor
from .assign_visitor import AssignVisitor
from .for_visitor import ForVisitor
from .frame_rotation_visitor import FrameRotationVisitor
from .measure_visitor import MeasureVisitor
from .play_visitor import PlayVisitor
from .reset_frame_visitor import ResetFrameVisitor
from .reset_phase_visitor import ResetPhaseVisitor
from .wait_visitor import WaitVisitor
from ...program_ast.align import Align
from ...program_ast.assign import Assign
from ...program_ast.frame_rotation_2pi import FrameRotation2Pi
from ...program_ast.measure import Measure
from ...program_ast.play import Play
from ...program_ast.program_for import For
from ...program_ast.reset_frame import ResetFrame
from ...program_ast.reset_phase import ResetPhase
from ...program_ast.wait import Wait

node_visitors = {
    Align: AlignVisitor(),
    Assign: AssignVisitor(),
    For: ForVisitor(),
    FrameRotation2Pi: FrameRotationVisitor(),
    Measure: MeasureVisitor(),
    Play: PlayVisitor(),
    ResetPhase: ResetPhaseVisitor(),
    ResetFrame: ResetFrameVisitor(),
    Wait: WaitVisitor(),
}


class NodeVisitor(Visitor):
    def visit(self, node: Node, context: Context):
        if type(node) in node_visitors:
            node.accept(node_visitors[type(node)], context)
        else:
            raise NotImplementedError(f"Unrecognised node type {type(node)}")
