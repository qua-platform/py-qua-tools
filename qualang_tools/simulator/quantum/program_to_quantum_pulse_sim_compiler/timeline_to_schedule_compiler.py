from typing import List, Dict

from qiskit import pulse
from qiskit.pulse import ScheduleBlock
from qiskit_dynamics import DynamicsBackend

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.context import Context
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.measure import Measure
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_IQ import TimelineIQ
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_schedules import \
    TimelineSchedules
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_single import \
    TimelineSingle
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.visitors.instruction_visitor import \
    InstructionVisitor


class TimelineToPulseScheduleCompiler:
    def compile(self, schedules: TimelineSchedules, backend: DynamicsBackend) -> List[ScheduleBlock]:
        schedules.prune_elements_if_passive()

        pulse_schedules = []

        instruction_visitor = InstructionVisitor()
        for i in range(schedules.num_schedules()):
            has_measurement = False
            with pulse.build(backend) as schedule:
                for element, timeline in schedules.get_slice(i).items():
                    if timeline.is_passive():
                        continue

                    if isinstance(timeline, TimelineSingle):
                        timelines = [timeline]
                    elif isinstance(timeline, TimelineIQ):
                        timelines = [timeline.I, timeline.Q]
                    else:
                        raise NotImplementedError()

                    for timeline in timelines:
                        with pulse.align_sequential():
                            context = Context(timeline)
                            for instruction in timeline.instructions:
                                if isinstance(instruction, Measure):
                                    has_measurement = True
                                instruction.accept(instruction_visitor, context)

            if len(schedule) > 0 and has_measurement:
                pulse_schedules.append(schedule)

        return pulse_schedules
