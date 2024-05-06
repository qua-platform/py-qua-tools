from .context import Context
from .schedules.timeline_schedules import TimelineSchedules
from ..architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap
from ..program_ast.program import Program
from .visitors.program_visitor import ProgramVisitor


class ProgramToTimelinesCompiler:
    def compile(self,
                qua_config: dict,
                program_tree: Program,
                channel_map: ConfigToTransmonPairBackendMap) -> TimelineSchedules:

        # compile the program AST into a runnable qiskit pulse simulator
        context = Context(qua_config=qua_config)
        context.create_timelines_for_each_element(channel_map)
        program_tree.accept(ProgramVisitor(), context)

        return context.schedules
