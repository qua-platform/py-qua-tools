from dataclasses import dataclass, field
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
class InstrumentChannelInput:
    io_type: Literal["input", "output"] = "input"

@dataclass
class InstrumentChannelOutput:
    io_type: Literal["input", "output"] = "output"

@dataclass
class InstrumentChannelDigital:
    signal_type = "digital"

@dataclass
class InstrumentChannelAnalog:
    signal_type = "analog"

@dataclass
class InstrumentChannelLfFem:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "lf-fem"

@dataclass
class InstrumentChannelMwFem:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "mw-fem"

@dataclass
class InstrumentChannelOpxPlus:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "opx+"

@dataclass
class InstrumentChannelOctave:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "octave"


@dataclass
class InstrumentChannelLfFemInput(
    InstrumentChannelAnalog,
    InstrumentChannelLfFem,
    InstrumentChannelInput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelLfFemOutput(
    InstrumentChannelAnalog,
    InstrumentChannelLfFem,
    InstrumentChannelOutput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelLfFemDigitalOutput(
    InstrumentChannelDigital,
    InstrumentChannelLfFem,
    InstrumentChannelOutput,
    InstrumentChannel
): pass


@dataclass
class InstrumentChannelMwFemInput(
    InstrumentChannelAnalog,
    InstrumentChannelMwFem,
    InstrumentChannelInput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelMwFemOutput(
    InstrumentChannelAnalog,
    InstrumentChannelMwFem,
    InstrumentChannelOutput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelMwFemDigitalOutput(
    InstrumentChannelDigital,
    InstrumentChannelMwFem,
    InstrumentChannelOutput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelOpxPlusInput(
    InstrumentChannelAnalog,
    InstrumentChannelOpxPlus,
    InstrumentChannelInput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelOpxPlusOutput(
    InstrumentChannelAnalog,
    InstrumentChannelOpxPlus,
    InstrumentChannelOutput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelOpxPlusDigitalOutput(
    InstrumentChannelDigital,
    InstrumentChannelOpxPlus,
    InstrumentChannelOutput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelOctaveInput(
    InstrumentChannelAnalog,
    InstrumentChannelOctave,
    InstrumentChannelInput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelOctaveOutput(
    InstrumentChannelAnalog,
    InstrumentChannelOctave,
    InstrumentChannelOutput,
    InstrumentChannel
): pass

@dataclass
class InstrumentChannelOctaveDigitalInput(
    InstrumentChannelDigital,
    InstrumentChannelOctave,
    InstrumentChannelInput,
    InstrumentChannel
): pass


AnyInstrumentChannel = Union[
    InstrumentChannelLfFemInput,
    InstrumentChannelLfFemOutput,
    InstrumentChannelMwFemInput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelOpxPlusInput,
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelOctaveInput,
    InstrumentChannelOctaveOutput,
]
