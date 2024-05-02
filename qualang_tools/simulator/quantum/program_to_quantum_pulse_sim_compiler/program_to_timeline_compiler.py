from .context import Context, ElementToTimelineMap
from ..architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap
from ..program_ast.program import Program
from .visitors.program_visitor import ProgramVisitor


class ProgramToTimelineCompiler:
    def compile(self,
                qua_config: dict,
                program_tree: Program,
                channel_map: ConfigToTransmonPairBackendMap) -> ElementToTimelineMap:

        # compile the program AST into a runnable qiskit pulse simulator
        context = Context(qua_config=qua_config)
        context.create_timelines_for_each_element(channel_map)
        program_tree.accept(ProgramVisitor(), context)

        return context.timelines
