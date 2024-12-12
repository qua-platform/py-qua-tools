from dataclasses import dataclass
from typing import Union, Literal, Callable


@dataclass(eq=False)
class InstrumentChannel:
    con: int
    port: int
    slot: Union[None, int] = None

    def __str__(self):
        return f'({", ".join([f"con{self.con}", f"{self.slot}" if self.slot else "", str(self.port)])})'

    def make_channel_filter(self) -> Callable[["InstrumentChannel"], bool]:
        return lambda channel: (
            (self.con is None or self.con == channel.con)
            and (self.slot is None or self.slot == channel.slot)
            and (self.port is None or self.port == channel.port)
        )


@dataclass(eq=False)
class InstrumentChannelInput:
    io_type: Literal["input", "output"] = "input"


@dataclass(eq=False)
class InstrumentChannelOutput:
    io_type: Literal["input", "output"] = "output"


@dataclass(eq=False)
class InstrumentChannelDigital:
    signal_type = "digital"


@dataclass(eq=False)
class InstrumentChannelAnalog:
    signal_type = "analog"


@dataclass(eq=False)
class InstrumentChannelLfFem:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "lf-fem"


@dataclass(eq=False)
class InstrumentChannelMwFem:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "mw-fem"


@dataclass(eq=False)
class InstrumentChannelOpxPlus:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "opx+"


@dataclass(eq=False)
class InstrumentChannelOctave:
    instrument_id: Literal["lf-fem", "mw-fem", "opx+", "octave"] = "octave"


@dataclass(eq=False)
class InstrumentChannelLfFemInput(
    InstrumentChannelAnalog, InstrumentChannelLfFem, InstrumentChannelInput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelLfFemOutput(
    InstrumentChannelAnalog, InstrumentChannelLfFem, InstrumentChannelOutput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelLfFemDigitalOutput(
    InstrumentChannelDigital, InstrumentChannelLfFem, InstrumentChannelOutput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelMwFemInput(
    InstrumentChannelAnalog, InstrumentChannelMwFem, InstrumentChannelInput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelMwFemOutput(
    InstrumentChannelAnalog, InstrumentChannelMwFem, InstrumentChannelOutput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelMwFemDigitalOutput(
    InstrumentChannelDigital, InstrumentChannelMwFem, InstrumentChannelOutput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelOpxPlusInput(
    InstrumentChannelAnalog, InstrumentChannelOpxPlus, InstrumentChannelInput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelOpxPlusOutput(
    InstrumentChannelAnalog, InstrumentChannelOpxPlus, InstrumentChannelOutput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelOpxPlusDigitalOutput(
    InstrumentChannelDigital, InstrumentChannelOpxPlus, InstrumentChannelOutput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelOctaveInput(
    InstrumentChannelAnalog, InstrumentChannelOctave, InstrumentChannelInput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelOctaveOutput(
    InstrumentChannelAnalog, InstrumentChannelOctave, InstrumentChannelOutput, InstrumentChannel
):
    pass


@dataclass(eq=False)
class InstrumentChannelOctaveDigitalInput(
    InstrumentChannelDigital, InstrumentChannelOctave, InstrumentChannelInput, InstrumentChannel
):
    pass


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
