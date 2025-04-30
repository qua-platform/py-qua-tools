from typing import List, Union

from .instrument_channel import (
    InstrumentChannelOctaveInput,
    InstrumentChannelOctaveOutput,
    InstrumentChannelOctaveDigitalInput,
    InstrumentChannelExternalMixerInput,
    InstrumentChannelExternalMixerOutput,
    InstrumentChannelExternalMixerDigitalInput,
)
from .instrument_channels import *
from .constants import *


class Instruments:
    """
    Class to add the static information about which QM instruments will be used
    in an experimental setup. Upon adding an instrument with one of the `add_` methods,
    its available channels will be enumerated and added individually to a public
    data structure of "available" channels. Later, these can be moved into a public
    data structure of "used" channels during allocation.
    """

    def __init__(self):
        self.used_channels = InstrumentChannels()
        self.available_channels = InstrumentChannels()

    def add_external_mixer(self, indices: Union[List[int], int]):
        """
        Add an external mixer, which is defined abstractly as a combined IQ-upconverter and
        IQ-downconverter.

        `indices` (List[int] | int): Can be one or more indices for one or more external mixers.
        """
        if isinstance(indices, int):
            indices = [indices]

        for index in indices:
            channel = InstrumentChannelExternalMixerInput(con=index, port=1)
            self.available_channels.add(channel)

            channel = InstrumentChannelExternalMixerOutput(con=index, port=1)
            self.available_channels.add(channel)

            channel = InstrumentChannelExternalMixerDigitalInput(con=index, port=1)
            self.available_channels.add(channel)

    def add_octave(self, indices: Union[List[int], int]):
        """
        Adds N octaves to the available instrument channels with the specified indices.

        This method handles both single integer indices and lists of indices.
        It creates and adds three types of channels: input, output, and digital input,
        for each octave index provided.

        Args:
            indices (Union[List[int], int]): Either a single integer or a list of integers
                representing the indices of the octaves to be added.
        """
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
        """
        Adds Low-Frequency Front End Module (LF-FEM) channels to the available channels of the
        instrument, labelled according to the specified `controller` index and `slot` indices.

        This method configures the LF-FEM input channels, output channels, and digital output
        channels for the given controller and for N LF-FEMs in the provided `slots`. If a single
        slot is provided as an integer, it will be converted into a list of slots internally.

        Args:
            controller (int): The controller ID associated with the LF FEM channels.
            slots (Union[List[int], int]): One or more slots for which the LF-FEMs reside in the
                OPX1000 chassis
        """
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
        """
        Adds microwave front-end module (MW-FEM) input, output, and digital output channels
        to the available channels for the given controller and specified slots.

        This method dynamically creates and registers MW-FEM channels based on the provided
        controller and slots. The slots can be specified as a single integer or as a list
        of integers. For each slot, the input, output, and digital output channels are
        instantiated and added to the existing pool of available channels.

        Args:
            controller (int): The identifier for the controller to which the MW FEMs should
                be added.
            slots (Union[List[int], int]): One or more slot numbers where the MW FEMs are
                located in the OPX1000 chassis. If given a single integer, it will be treated
                as a list with one slot.
        """
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
        """
        Adds OPX+ controllers and their associated channels to the available pool of
        channels. The method processes input, output, and digital output ports for
        each specified controller. Digital output ports are added in a specific order
        (odd-numbered ports first, followed by even-numbered ports) for convenience
        and potential compatibility with octave connectivity.

        Note that digital output ports are added in the following order: 1, 3, 5, 7, 9,
        2, 4, 6, 8, 10. This ordering corresponds to the physical order of the channels,
        starting from left-to-right, then top-to-bottom.

        Args:
            controllers (Union[List[int], int]): A list of controller IDs or a single
                controller ID. The controllers represent the OPX+ devices to be
                configured and their ports to be allocated.
        """
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
