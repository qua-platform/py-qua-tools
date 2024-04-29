from dataclasses import dataclass, field
from typing import Literal, List, Dict

Element = str
InstructionType = Literal['play', 'acquire', 'delay']


@dataclass
class Instruction:
    type: InstructionType
    duration: int
    args: dict


@dataclass
class Timeline:
    qubit_index: int
    drive_channel: int
    instructions: List[Instruction] = field(default_factory=list)
    current_time: float = 0

    def add_instruction(self, type: InstructionType, duration: int, **args):
        self.current_time += duration
        self.instructions.append(
            Instruction(
                type=type,
                duration=duration,
                args=args
            )
        )


def align(timelines: List[Timeline]):
    latest_time = 0
    for timeline in timelines:
        latest_time = max(latest_time, timeline.current_time)

    for timeline in timelines:
        time_delta = latest_time - timeline.current_time
        if time_delta != 0:
            timeline.add_instruction('delay', time_delta)


Timelines = Dict[Element, List[Timeline]]


def get_timeline(element: str, timelines: Timelines):
    return timelines[element][-1]


def restart_qubit_timelines(element: str, timelines: Timelines):
    qubit_index = get_timeline(element, timelines).qubit_index
    for timeline in timelines.values():
        if timeline[-1].qubit_index == qubit_index:
            timeline.append(Timeline(
                qubit_index=qubit_index,
                drive_channel=timeline[-1].drive_channel
            ))