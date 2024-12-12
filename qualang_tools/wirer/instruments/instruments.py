from typing import List, Union

from .instrument_channel import (
    InstrumentChannelOctaveInput,
    InstrumentChannelOctaveOutput,
    InstrumentChannelOctaveDigitalInput,
)
from .instrument_channels import *
from .constants import *


class Instruments:
    """
    Class to add the static information about which QM instruments will be used
    in an experimental setup. Upon adding an instrument, its available channels
    will be enumerated and added individually to a stack of free channels.
    """

    def __init__(self):
        self.used_channels = InstrumentChannels()
        self.available_channels = InstrumentChannels()

    def add_octave(self, indices: Union[List[int], int]):
        if isinstance(indices, int):
            indices = [indices]

        for index in indices:
            for port in range(1, NUM_OCTAVE_INPUT_PORTS + 1):
                channel = InstrumentChannelOctaveInput(con=index, port=port)
                self.available_channels.add(channel)

            for port in range(1, NUM_OCTAVE_OUTPUT_PORTS + 1):
                channel = InstrumentChannelOctaveOutput(con=index, port=port)
                self.available_channels.add(channel)

            for port in range(1, NUM_OCTAVE_DIGITAL_INPUT_PORTS + 1):
                channel = InstrumentChannelOctaveDigitalInput(con=index, port=port)
                self.available_channels.add(channel)

    def add_lf_fem(self, controller: int, slots: Union[List[int], int]):
        if isinstance(slots, int):
            slots = [slots]

        for slot in slots:
            for port in range(1, NUM_LF_FEM_INPUT_PORTS + 1):
                channel = InstrumentChannelLfFemInput(con=controller, slot=slot, port=port)
                self.available_channels.add(channel)

            for port in range(1, NUM_LF_FEM_OUTPUT_PORTS + 1):
                channel = InstrumentChannelLfFemOutput(con=controller, slot=slot, port=port)
                self.available_channels.add(channel)

            for port in range(1, NUM_LF_FEM_DIGITAL_OUTPUT_PORTS + 1):
                channel = InstrumentChannelLfFemDigitalOutput(con=controller, slot=slot, port=port)
                self.available_channels.add(channel)

    def add_mw_fem(self, controller: int, slots: Union[List[int], int]):
        if isinstance(slots, int):
            slots = [slots]

        for slot in slots:
            for port in range(1, NUM_MW_FEM_INPUT_PORTS + 1):
                channel = InstrumentChannelMwFemInput(con=controller, slot=slot, port=port)
                self.available_channels.add(channel)

            for port in range(1, NUM_MW_FEM_OUTPUT_PORTS + 1):
                channel = InstrumentChannelMwFemOutput(con=controller, slot=slot, port=port)
                self.available_channels.add(channel)

            for port in range(1, NUM_MW_FEM_OUTPUT_PORTS + 1):
                channel = InstrumentChannelMwFemDigitalOutput(con=controller, slot=slot, port=port)
                self.available_channels.add(channel)

    def add_opx_plus(self, controllers: Union[List[int], int]):
        if isinstance(controllers, int):
            controllers = [controllers]

        for controller in controllers:
            for port in range(1, NUM_OPX_PLUS_INPUT_PORTS + 1):
                channel = InstrumentChannelOpxPlusInput(con=controller, port=port)
                self.available_channels.add(channel)

            for port in range(1, NUM_OPX_PLUS_OUTPUT_PORTS + 1):
                channel = InstrumentChannelOpxPlusOutput(con=controller, port=port)
                self.available_channels.add(channel)

            # add odd first for octave connectivity (top row is more convenient)
            for port in range(1, NUM_OPX_PLUS_DIGITAL_OUTPUT_PORTS + 1, 2):
                channel = InstrumentChannelOpxPlusDigitalOutput(con=controller, port=port)
                self.available_channels.add(channel)

            # then add evens
            for port in range(2, NUM_OPX_PLUS_DIGITAL_OUTPUT_PORTS + 1, 2):
                channel = InstrumentChannelOpxPlusDigitalOutput(con=controller, port=port)
                self.available_channels.add(channel)
