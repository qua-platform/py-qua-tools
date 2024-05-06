from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.delay import Delay
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.instruction import Instruction
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.phase_offset import PhaseOffset
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.play import Play
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.reset_phase import ResetPhase
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.reset_phase_visitor import \
    ResetPhaseVisitor
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.visitor import Visitor


class InstructionVisitor(Visitor):
    def visit(self, instruction: Instruction, instruction_context: Context):
        # local imports to avoid circular dependency
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.delay_visitor import \
            DelayVisitor
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.measure_visitor import \
            MeasureVisitor
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.phase_offset_visitor import \
            PhaseOffsetVisitor
        from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.play_visitor import \
            PlayVisitor
        # from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.simultaneous_visitor import \
        #     SimultaneousVisitor

        visitors = {
            Play: PlayVisitor(),
            Measure: MeasureVisitor(),
            Delay: DelayVisitor(),
            ResetPhase: ResetPhaseVisitor(),
            PhaseOffset: PhaseOffsetVisitor(),
            # Simultaneous: SimultaneousVisitor()
        }

        if type(instruction) in visitors:
            instruction.accept(visitors[type(instruction)], instruction_context)
        else:
            raise NotImplementedError(f"Unrecognized instruction type {instruction}")
