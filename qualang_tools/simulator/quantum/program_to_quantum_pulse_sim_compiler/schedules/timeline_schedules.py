from typing import Dict, List

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline import Timeline
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_IQ import TimelineIQ
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.schedules.timeline_single import \
    TimelineSingle

Element = str
TimelineSchedule = List[Timeline]


class TimelineSchedules:
    map: Dict[Element, TimelineSchedule] = {}

    def get_elements(self) -> List[Element]:
        return list(self.map.keys())

    def get_timeline(self, element: Element) -> Timeline:
        return self.map[element][-1]

    def get_qubit_index(self, element: Element) -> int:
        return self.get_timeline(element).qubit_index

    def get_slice(self, index: int) -> Dict[Element, Timeline]:
        return {
            element: self.map[element][index]
            for element in self.map
        }

    def align(self, elements: List[Element]):
        if len(elements) == 0:
            elements = list(self.map.keys())  # global align

        latest_time = 0
        timelines = self.get_slice(-1).items()
        for element, timeline in timelines:
            if element in elements:
                latest_time = max(latest_time, timeline.current_time)

        for element, timeline in timelines:
            if element in elements:
                time_delta = latest_time - timeline.current_time
                if time_delta != 0:
                    timeline.delay(time_delta)

    def restart_schedules_on_same_qubit_as(self, element: str):
        qubit_index = self.get_qubit_index(element)
        for schedule in self.map.values():
            first_timeline = schedule[0]
            if first_timeline.qubit_index == qubit_index:
                if isinstance(first_timeline, TimelineSingle):
                    schedule.append(
                        TimelineSingle(
                            qubit_index=first_timeline.qubit_index,
                            pulse_channel=first_timeline.pulse_channel
                        )
                    )
                elif isinstance(first_timeline, TimelineIQ):
                    schedule.append(
                        TimelineIQ(
                            qubit_index=first_timeline.qubit_index,
                            pulse_channel_i=first_timeline.I.pulse_channel,
                            pulse_channel_q=first_timeline.Q.pulse_channel
                        )
                    )

    def prune_elements_if_passive(self):
        self.map = {
            element: schedule
            for element, schedule in self.map.items()
            if not all([timeline.is_passive() for timeline in schedule])
        }

    def _validate_schedule_synchronization(self):
        schedule_lengths = [len(schedule) for schedule in self.map.values()]
        if not all([length / schedule_lengths[0] == 1 for length in schedule_lengths]):
            schedule_lengths_str = "\n".join([
                f"{element}: {len(schedule)}" for element, schedule in self.map.items()
            ])
            raise ValueError(f"Not all schedule lengths are the same, got \n{schedule_lengths_str}")

    def num_schedules(self) -> int:
        self._validate_schedule_synchronization()

        return len(list(self.map.values())[0])
