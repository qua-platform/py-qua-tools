from dataclasses import dataclass
from typing import Union, Literal, Callable


@dataclass
class InstrumentChannel:
    con: int
    port: int
    slot: Union[None, int] = None

    def __str__(self):
        return f'({", ".join([f"con{self.con}", f"{self.slot}" if self.slot else "", str(self.port)])})'

    def make_channel_filter(self) -> Callable[['InstrumentChannel'], bool]:
        return lambda channel: (
            (self.con is None or self.con == channel.con) and
            (self.slot is None or self.slot == channel.slot) and
            (self.port is None or self.port == channel.port)
        )


@dataclass
class InstrumentChannelInput(InstrumentChannel):
    io_type: Literal["input", "output"] = "input"


@dataclass
class InstrumentChannelOutput(InstrumentChannel):
    io_type: Literal["input", "output"] = "output"


@dataclass
class InstrumentChannelLfFemInput(InstrumentChannelInput):
    instrument_id = "lf-fem"


@dataclass
class InstrumentChannelLfFemOutput(InstrumentChannelOutput):
    instrument_id = "lf-fem"


@dataclass
class InstrumentChannelMwFemInput(InstrumentChannelInput):
    instrument_id = "mw-fem"


@dataclass
class InstrumentChannelMwFemOutput(InstrumentChannelOutput):
    instrument_id = "mw-fem"


@dataclass
class InstrumentChannelOpxPlusInput(InstrumentChannelInput):
    instrument_id = "opx+"


@dataclass
class InstrumentChannelOpxPlusOutput(InstrumentChannelOutput):
    instrument_id = "opx+"


@dataclass
class InstrumentChannelOctaveInput(InstrumentChannelInput):
    instrument_id = "octave"


class InstrumentChannelOctaveOutput(InstrumentChannelOutput):
    instrument_id = "octave"
