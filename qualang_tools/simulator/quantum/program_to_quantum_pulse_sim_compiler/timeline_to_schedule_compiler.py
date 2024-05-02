from typing import List, Dict

from qiskit import pulse
from qiskit.pulse import ScheduleBlock
from qiskit_dynamics import DynamicsBackend

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.context import ElementToTimelineMap
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import Timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.visitors.instruction_visitor import \
    InstructionVisitor


class TimelineToPulseScheduleCompiler:
    def compile(self, timelines: ElementToTimelineMap, backend: DynamicsBackend) -> List[ScheduleBlock]:
        # filter empty timelines
        timelines = {k: v for k, v in timelines.items() if not all([t.is_empty() for t in v]) }
        timeline_lengths = [len(timeline) for timeline in timelines.values()]
        assert all([length / timeline_lengths[0] == 1 for length in timeline_lengths])

        schedules = []
        instruction_visitor = InstructionVisitor()
        for i in range(timeline_lengths[0]):
            has_measurement = False
            with pulse.build(backend) as schedule:
                for channel_timelines in timelines.values():
                    if channel_timelines[i].is_empty():
                        continue
                    with pulse.align_sequential():
                        for instruction in channel_timelines[i].instructions:
                            if isinstance(instruction, Measure):
                                has_measurement = True
                            instruction_visitor.visit(instruction, channel_timelines[i].pulse_channel)

            if len(schedule) > 0 and has_measurement:
                schedules.append(schedule)

        return schedules
