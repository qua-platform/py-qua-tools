"""
The purpose of this module is to compile a sequence of wiring specifications
into potential channel specifications, then to allocate them to the first valid
combination of instrument channels.
"""

import copy
from typing import List

from .channel_specs import (
    ChannelSpecLfFemSingle,
    ChannelSpecOpxPlusSingle,
    ChannelSpecMwFemSingle,
    ChannelSpecLfFemBaseband,
    ChannelSpecOctave,
    ChannelSpecExternalMixer,
    ChannelSpecOpxPlusBaseband,
    ChannelSpecMwFemDigital,
    ChannelSpecLfFemDigital,
    ChannelSpecOctaveDigital,
    ChannelSpecOpxPlusDigital,
    ChannelSpecExternalMixerDigital,
)
from .wirer_assign_channels_to_spec import assign_channels_to_spec
from .wirer_exceptions import ConstraintsTooStrictException, NotEnoughChannelsException
from ..connectivity.channel_spec import ChannelSpec
from ..instruments import Instruments
from ..connectivity import Connectivity
from ..connectivity.wiring_spec import WiringSpec, WiringFrequency, WiringLineType


def allocate_wiring(
    connectivity: Connectivity,
    instruments: Instruments,
    block_used_channels: bool = True,
    clear_wiring_specifications: bool = True,
):
    """
    Allocates available instrument channels to quantum elements based on their wiring specifications.

    This function takes the wiring specifications from the provided `Connectivity` instance and attempts
    to allocate channels for each specification to the available instrument channels within the `Instruments` instance.

    The allocation is done in a sequence based on the line types specified in the `line_type_fill_order`. The function
    handles different frequency requirements, either DC or RF, and manages the reuse of available channels depending on
    the `block_used_channels` flag.

    The allocation process involves the following steps:
    1. The function iterates over the wiring specifications (`specs`) based on their `line_type`, attempting to allocate
       channels for each `WiringSpec`.
    2. For each specification, the relevant allocation function (`_allocate_wiring`) is called to allocate DC or RF channels.
    3. If `clear_wiring_specifications` is `True`, the specifications are cleared after the allocation.
    4. If `block_used_channels` is `False`, any channels that were previously used but are no longer allocated are returned
       to the available channels list.

    Args:
        connectivity (Connectivity): An instance of the `Connectivity` class containing the wiring specifications to be allocated.
        instruments (Instruments): An instance of the `Instruments` class that manages available and used channels.
        block_used_channels (bool, optional): If `True`, prevents previously used channels from being returned to the available pool.
            Defaults to `True`.
        clear_wiring_specifications (bool, optional): If `True`, clears the list of wiring specifications in `connectivity`
            after allocation. Defaults to `True`.

    Raises:
        ConstraintsTooStrictException: If the constraints for a wiring specification are too strict, preventing allocation.
        NotEnoughChannelsException: If there are not enough available channels to satisfy the wiring specification.
    """

    line_type_fill_order = [
        WiringLineType.RESONATOR,
        WiringLineType.DRIVE,
        WiringLineType.FLUX,
        WiringLineType.CHARGE,
        WiringLineType.COUPLER,
        WiringLineType.CROSS_RESONANCE,
        WiringLineType.ZZ_DRIVE,
    ]

    specs = connectivity.specs

    used_channel_cache = copy.deepcopy(instruments.used_channels)

    specs_with_untyped_lines = []
    for line_type in line_type_fill_order:
        for spec in specs:
            if spec.line_type not in line_type_fill_order:
                specs_with_untyped_lines.append(spec)
            if spec.line_type == line_type:
                _allocate_wiring(spec, instruments)

    # remove duplicates
    specs_with_untyped_lines = list(dict.fromkeys(specs_with_untyped_lines))
    for spec in specs_with_untyped_lines:
        _allocate_wiring(spec, instruments)

    if clear_wiring_specifications:
        connectivity.specs = []

    if not block_used_channels:
        for channel_type, used_channels in instruments.used_channels.items():
            for i, used_channel in enumerate(reversed(used_channels)):
                if used_channel not in used_channel_cache:
                    instruments.available_channels.insert(0, used_channel)
                    instruments.used_channels.remove(used_channel)


def _allocate_wiring(spec: WiringSpec, instruments: Instruments):
    if spec.frequency == WiringFrequency.DC:
        allocate_dc_channels(spec, instruments)

    elif spec.frequency == WiringFrequency.RF:
        allocate_rf_channels(spec, instruments)

    elif spec.frequency == WiringFrequency.DO:
        allocate_do_channels(spec, instruments)

    else:
        raise NotImplementedError()


def allocate_dc_channels(spec: WiringSpec, instruments: Instruments):
    """
    Try to allocate DC channels to an LF-FEM or OPX+ to satisfy the spec.
    """
    dc_specs = [
        # LF-FEM, Single analog output
        ChannelSpecLfFemSingle() & ChannelSpecLfFemDigital(),
        # OPX+, Single analog output
        ChannelSpecOpxPlusSingle() & ChannelSpecOpxPlusDigital()
    ]

    allocate_channels(spec, dc_specs, instruments, same_con=True, same_slot=True)


def allocate_rf_channels(spec: WiringSpec, instruments: Instruments):
    """
    Try to allocate RF channels to a MW-FEM. If that doesn't work, look for a
    combination of LF-FEM I/Q and Octave channels, or OPX+ I/Q and Octave
    channels.
    """
    rf_specs = [
        # MW-FEM, Single RF output
        ChannelSpecMwFemSingle() & ChannelSpecMwFemDigital(),
        # LF-FEM I/Q output with Octave for upconversion
        ChannelSpecLfFemBaseband() & ChannelSpecLfFemDigital() & ChannelSpecOctave() & ChannelSpecOctaveDigital(),
        # LF-FEM I/Q output with External Mixer for upconversion
        ChannelSpecLfFemBaseband()
        & ChannelSpecLfFemDigital()
        & ChannelSpecExternalMixer()
        & ChannelSpecExternalMixerDigital(),
        # OPX+ I/Q output with Octave for upconversion
        ChannelSpecOpxPlusBaseband() & ChannelSpecOpxPlusDigital() & ChannelSpecOctave() & ChannelSpecOctaveDigital(),
        # OPX+ I/Q output with External Mixer for upconversion
        ChannelSpecOpxPlusBaseband()
        & ChannelSpecOpxPlusDigital()
        & ChannelSpecExternalMixer()
        & ChannelSpecExternalMixerDigital(),
    ]

    allocate_channels(spec, rf_specs, instruments, same_con=True, same_slot=True)


def allocate_do_channels(spec: WiringSpec, instruments: Instruments):
    """
    Try to allocate DC channels to an LF-FEM or OPX+ to satisfy the spec.
    """
    dc_specs = [
        # LF-FEM, Single digital output
        ChannelSpecLfFemDigital(),
        # OPX+, Single digital output
        ChannelSpecOpxPlusDigital()
    ]

    allocate_channels(spec, dc_specs, instruments, same_con=True, same_slot=True)

def allocate_channels(
    wiring_spec: WiringSpec, channel_specs: List[ChannelSpec], instruments: Instruments, same_con: bool, same_slot: bool
):
    mask_failures = 0
    for channel_spec in channel_specs:
        channel_spec = channel_spec.filter_by_wiring_spec(wiring_spec)
        if wiring_spec.constraints:
            constraints = wiring_spec.constraints.filter_by_wiring_spec(wiring_spec)
            if not channel_spec.apply_constraints(constraints):
                mask_failures += 1
                continue
        if assign_channels_to_spec(
            wiring_spec, instruments, channel_spec.channel_templates, same_con=same_con, same_slot=same_slot
        ):
            return

    if mask_failures == len(channel_specs):
        raise ConstraintsTooStrictException(wiring_spec, wiring_spec.constraints)
    else:
        raise NotEnoughChannelsException(wiring_spec)
