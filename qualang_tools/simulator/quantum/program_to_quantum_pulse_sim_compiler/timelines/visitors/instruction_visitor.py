from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.delay import Delay
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.instruction import Instruction
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.phase_offset import PhaseOffset
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.play import Play
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.simultaneous import Simultaneous
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.visitor import Visitor


class InstructionVisitor(Visitor):
    def visit(self, instruction: Instruction, drive_channel: int):
        # local imports to avoid circular dependency
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.delay_visitor import \
            DelayVisitor
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.measure_visitor import \
            MeasureVisitor
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.phase_offset_visitor import \
            PhaseOffsetVisitor
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.play_visitor import \
            PlayVisitor
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.simultaneous_visitor import \
            SimultaneousVisitor

        visitors = {
            Play: PlayVisitor(),
            Measure: MeasureVisitor(),
            Delay: DelayVisitor(),
            PhaseOffset: PhaseOffsetVisitor(),
            Simultaneous: SimultaneousVisitor()
        }

        if type(instruction) in visitors:
            instruction.accept(visitors[type(instruction)], drive_channel)
        else:
            raise NotImplementedError(f"Unrecognized instruction type {instruction}")
