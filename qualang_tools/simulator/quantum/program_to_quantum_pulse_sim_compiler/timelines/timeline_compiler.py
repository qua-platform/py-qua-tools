from typing import List, Dict

from qiskit import pulse
from qiskit.pulse import ScheduleBlock
from qiskit_dynamics import DynamicsBackend

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import Timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.instruction_visitor import \
    InstructionVisitor


class TimelineCompiler:
    def compile(self, timelines: Dict[str, List[Timeline]], backend: DynamicsBackend) -> List[ScheduleBlock]:
        timeline_lengths = [len(timeline) for timeline in timelines.values()]
        assert all([length / timeline_lengths[0] == 1 for length in timeline_lengths])

        schedules = []
        instruction_visitor = InstructionVisitor()
        for i in range(timeline_lengths[0]):
            with pulse.build(backend) as schedule:
                for channel_timelines in timelines.values():
                    with pulse.align_sequential():
                        for instruction in channel_timelines[i].instructions:
                            instruction_visitor.visit(instruction, channel_timelines[i].drive_channel)

            if len(schedule) > 0:
                schedules.append(schedule)

        return schedules
