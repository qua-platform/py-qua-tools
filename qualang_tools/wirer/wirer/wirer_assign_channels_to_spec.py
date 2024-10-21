from typing import List

from qualang_tools.wirer.connectivity.wiring_spec import WiringSpec
from qualang_tools.wirer.instruments import Instruments
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

    return len(candidate_channels) == len(channel_templates)


def _assign_channels_to_spec(
    spec: WiringSpec,
    instruments: Instruments,
    channel_templates: List[ChannelTemplate],
    same_con: bool,
    same_slot: bool,
    allocated_channels=None,
):
    """
    Recursive function to find any valid combination of channel allocations
    given a wiring specification, a stack of available channels in the
    instruments setup, and a list of desired channel types.
    """
    if allocated_channels is None:
        allocated_channels = []

    # extract the lead/initial channel type
    target_channel_template = channel_templates[0]

    # filter available channels according to the specification
    available_channels = list(
        filter(
            target_channel_template.make_channel_filter(),  # filter function
            instruments.available_channels.get(type(target_channel_template), []),  # iterable
        )
    )

    candidate_channels = []
    for channel in available_channels:
        # make sure to not re-allocate a channel
        if channel in allocated_channels:
            continue

        candidate_channels = [channel]

        # base case: all channels allocated properly
        if len(channel_templates) == 1:
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
                )

            candidate_channels.extend(subsequent_channels)

            # without a candidate channel for every type, try the next available channel
            if len(candidate_channels) == len(channel_templates):
                break

            # otherwise, a successful allocation has been made
            else:
                continue

    return candidate_channels
