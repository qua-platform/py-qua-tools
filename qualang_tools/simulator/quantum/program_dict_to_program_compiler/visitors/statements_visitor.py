from typing import List

from .align_visitor import AlignVisitor
from .assign_visitor import AssignVisitor
from .for_visitor import ForVisitor
from .frame_rotation_visitor import FrameRotationVisitor
from .measure_visitor import MeasureVisitor
from .play_visitor import PlayVisitor
from .reset_frame_visitor import ResetFrameVisitor
from .reset_phase_visitor import ResetPhaseVisitor
from .save_visitor import SaveVisitor
from .strict_timing_visitor import StrictTimingVisitor
from .visitor import Visitor
from .wait_visitor import WaitVisitor
from ...program_ast.node import Node


node_types_and_visitors = {
    'align': AlignVisitor(),
    'assign': AssignVisitor(),
    'for': ForVisitor(),
    'strictTiming': StrictTimingVisitor(),
    'measure': MeasureVisitor(),
    'play': PlayVisitor(),
    'resetFrame': ResetFrameVisitor(),
    'resetPhase': ResetPhaseVisitor(),
    'save': SaveVisitor(),
    'wait': WaitVisitor(),
    'zRotation': FrameRotationVisitor(),
}


class StatementsVisitor(Visitor):
    def visit(self, d: dict) -> List[Node]:
        inner_nodes = []
        for node_dict in d['statements']:
            assert len(node_dict.keys()) == 1
            node_type = list(node_dict.keys())[0]

            if node_type in node_types_and_visitors:
                visited_node = node_types_and_visitors[node_type].visit(node_dict[node_type])
            else:
                raise NotImplementedError(f'Unrecognised node type {node_type}')

            inner_nodes.extend(visited_node)

        return inner_nodes
