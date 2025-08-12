from typing import List

from qualang_tools.wirer.connectivity.wiring_spec import WiringSpec
from qualang_tools.wirer.instruments import Instruments
from qualang_tools.wirer.instruments.instrument_channel import InstrumentChannelMwFemOutput, InstrumentChannelLfFem, \
    InstrumentChannelLfFemOutput, InstrumentChannelOpxPlusOutput
from qualang_tools.wirer.instruments.instrument_pulsers import Pulser
from qualang_tools.wirer.wirer.channel_specs import ChannelTemplate
from qualang_tools.wirer.wirer.context_manager_multi_object_temp_attr_setting import MultiObjectTempAttrUpdater


def assign_channels_to_spec(
    spec: WiringSpec,
    instruments: Instruments,
    channel_templates: List[ChannelTemplate],
    same_con: bool = False,
    same_slot: bool = False,
) -> bool:
    candidate_channels = _assign_channels_to_spec(spec, instruments, channel_templates, same_con, same_slot)

    # if candidate channels satisfy all the required channel types
    if len(candidate_channels) == len(channel_templates):
        for channel in candidate_channels:
            # remove candidate channel from stack of available channels
            instruments.used_channels.add(channel)
            instruments.available_channels[type(channel)].remove(channel)
            for element in spec.elements:
                # assign channel to the specified element
                if spec.line_type not in element.channels:
                    element.channels[spec.line_type] = []
                element.channels[spec.line_type].append(channel)
                # Keep track of the pulsers.
                if type(channel) is InstrumentChannelMwFemOutput:
                    instruments.available_pulsers.remove_by_slot(channel.con, channel.slot)
                    instruments.available_pulsers.remove_by_slot(channel.con, channel.slot)
                    instruments.used_pulsers.add(Pulser(channel.con, channel.slot))
                    instruments.used_pulsers.add(Pulser(channel.con, channel.slot))
                elif type(channel) is InstrumentChannelLfFemOutput or type(channel) is InstrumentChannelOpxPlusOutput:
                    instruments.available_pulsers.remove_by_slot(channel.con, channel.slot)
                    instruments.used_pulsers.add(Pulser(channel.con, channel.slot))

    return len(candidate_channels) == len(channel_templates)


def _assign_channels_to_spec(
    spec: WiringSpec,
    instruments: Instruments,
    channel_templates: List[ChannelTemplate],
    same_con: bool,
    same_slot: bool,
    allocated_channels=None,
    available_pulsers=None,
):
    """
    Recursive function to find any valid combination of channel allocations
    given a wiring specification, a stack of available channels in the
    instruments setup, and a list of desired channel types.
    """
    if allocated_channels is None:
        allocated_channels = []

    if available_pulsers is None:
        available_pulsers = instruments.available_pulsers.deepcopy()

    # extract the lead/initial channel type
    target_channel_template = channel_templates[0]

    # filter available channels according to the specification
    available_channels = list(
        filter(
            target_channel_template.make_channel_filter(),  # filter function
            instruments.available_channels.get(type(target_channel_template), []),  # iterable
        )
    )

    # filter out all channels, that have no more pulsers available on the device
    channels_with_pulsers = (InstrumentChannelLfFemOutput, InstrumentChannelMwFemOutput, InstrumentChannelOpxPlusOutput)
    available_channels = [
        channel
        for channel in available_channels
        if (isinstance(channel, channels_with_pulsers) and available_pulsers.filter_by_slot(channel.con, channel.slot)
            ) or not isinstance(channel, channels_with_pulsers)
    ]

    candidate_channels = []
    for channel in available_channels:
        # make sure to not re-allocate a channel
        if channel in allocated_channels:
            continue

        candidate_channels = [channel]

        # base case: all channels allocated properly
        if len(channel_templates) == 1:
            if type(channel) is InstrumentChannelMwFemOutput:
                available_pulsers.remove(instruments.available_pulsers[channel.con, channel.slot])
                available_pulsers.remove(instruments.available_pulsers[channel.con, channel.slot])
            elif type(channel) is InstrumentChannelLfFemOutput or type(channel) is InstrumentChannelOpxPlusOutput:
                pass
                available_pulsers.remove(instruments.available_pulsers[channel.con, channel.slot])
            break

        # recursive case: allocate remaining channels
        else:
            templates_with_same_instr = [
                template for template in channel_templates[1:] if template.instrument_id == channel.instrument_id
            ]
            with MultiObjectTempAttrUpdater(templates_with_same_instr, con=channel.con, slot=channel.slot):
                # recursively allocate the remaining channels
                subsequent_channels = _assign_channels_to_spec(
                    spec,
                    instruments,
                    channel_templates[1:],
                    same_con,
                    same_slot,
                    allocated_channels=candidate_channels,
                    available_pulsers=available_pulsers,
                )

            candidate_channels.extend(subsequent_channels)

            # without a candidate channel for every type, try the next available channel
            if len(candidate_channels) == len(channel_templates):
                break

            # otherwise, a successful allocation has been made
            else:
                continue

    return candidate_channels
