from dataclasses import asdict
from typing import Type

from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannel,
    InstrumentChannelLfFemInput,
    InstrumentChannelLfFemOutput,
    InstrumentChannelMwFemInput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelOpxPlusInput,
    InstrumentChannelOpxPlusOutput,
    AnyInstrumentChannel,
    InstrumentChannelLfFemDigitalOutput,
    InstrumentChannelMwFemDigitalOutput,
    InstrumentChannelOpxPlusDigitalOutput,
)

CHANNELS_OPX_PLUS = [
    InstrumentChannelOpxPlusInput,
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelOpxPlusDigitalOutput,
]

CHANNELS_OPX_1000 = [
    InstrumentChannelLfFemInput,
    InstrumentChannelLfFemOutput,
    InstrumentChannelLfFemDigitalOutput,
    InstrumentChannelMwFemInput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelMwFemDigitalOutput,
]


class InstrumentChannels:
    """
    Collection of "stack" data-structures organized by channel type.
    Each entry contains a list of instrument channels. This wrapper
    can be interacted with as if it were the underlying stack dictionary.
    """

    def __init__(self):
        self.stack = {}

    def check_if_already_occupied(self, channel: AnyInstrumentChannel):
        for channel_type in self.stack:
            for existing_channel in self.stack[channel_type]:
                if (
                    channel.con == existing_channel.con
                    and channel.slot == existing_channel.slot
                    and channel.port == existing_channel.port
                    and channel.io_type == existing_channel.io_type
                    and channel.signal_type == existing_channel.signal_type
                ):
                    if channel.slot is None:
                        if type(channel) != type(existing_channel):
                            pass
                        else:
                            raise ValueError(
                                f"{channel.io_type} channel on con{channel.con}, "
                                f"port {channel.port} is already occupied."
                            )
                    else:
                        raise ValueError(
                            f"{channel.io_type} channel on con{channel.con}, "
                            f"slot {channel.slot}, port {channel.port} is already occupied."
                        )

    def check_if_mixing_opx_1000_and_opx_plus(self, channel: InstrumentChannel):
        if type(channel) in CHANNELS_OPX_1000:
            for channel_type in CHANNELS_OPX_PLUS:
                if channel_type in self.stack:
                    raise ValueError("Can't add an FEM to a setup with an OPX+.")
        elif type(channel) in CHANNELS_OPX_PLUS:
            for channel_type in CHANNELS_OPX_1000:
                if channel_type in self.stack:
                    raise ValueError("Can't add an OPX+ to a setup with an OPX1000 FEM.")

    def insert(self, pos: int, channel: InstrumentChannel):
        self.check_if_already_occupied(channel)
        self.check_if_mixing_opx_1000_and_opx_plus(channel)

        channel_type = type(channel)
        if channel_type not in self.stack:
            self.stack[channel_type] = []

        self.stack[channel_type].insert(pos, channel)

    def add(self, channel: InstrumentChannel):
        self.check_if_already_occupied(channel)
        self.check_if_mixing_opx_1000_and_opx_plus(channel)

        channel_type = type(channel)
        if channel_type not in self.stack:
            self.stack[channel_type] = []

        self.stack[channel_type].append(channel)

    def pop(self, channel: Type[InstrumentChannel]):
        return self.stack[channel].pop(0)

    def remove(self, channel: InstrumentChannel):
        return self.stack[type(channel)].remove(channel)

    def get(self, key: InstrumentChannel, fallback=None):
        return self.stack.get(key, fallback)

    def __getitem__(self, item):
        return self.stack[item]

    def __iter__(self):
        return iter(self.stack)

    def __contains__(self, item: InstrumentChannel):
        for channel_type in self.stack:
            if asdict(item) in [asdict(channel) for channel in self.stack[channel_type]]:
                return True
        return False

    def items(self):
        return self.stack.items()
