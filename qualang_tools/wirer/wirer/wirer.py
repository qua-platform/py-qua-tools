from .channel_specs import ChannelSpecLfFemSingle, ChannelSpecOpxPlusSingle, ChannelSpecMwFemSingle, \
    ChannelSpecLfFemBaseband, ChannelSpecOctave, ChannelSpecOpxPlusBaseband
from .wirer_assign_channels_to_spec import assign_channels_to_spec
from .wirer_exception import WirerException
from ..instruments import Instruments
from ..connectivity import Connectivity
from ..connectivity.wiring_spec import WiringSpec, WiringFrequency, WiringLineType


def allocate_wiring(connectivity: Connectivity, instruments: Instruments):
    line_type_fill_order = [
        WiringLineType.RESONATOR,
        WiringLineType.DRIVE,
        WiringLineType.FLUX,
        WiringLineType.COUPLER,
    ]

    specs = connectivity.specs
    for line_type in line_type_fill_order:
        for spec in specs:
            if spec.line_type == line_type:
                _allocate_channels(spec, instruments)


def _allocate_channels(spec: WiringSpec, instruments: Instruments):
    if spec.frequency == WiringFrequency.DC:
        allocate_dc_channels(spec, instruments)

    elif spec.frequency == WiringFrequency.RF:
        allocate_rf_channels(spec, instruments)

    else:
        raise NotImplementedError()


def allocate_dc_channels(spec: WiringSpec, instruments: Instruments):
    """
    Try to allocate DC channels to an LF-FEM or OPX+ to satisfy the spec.
    """
    if not spec.channel_specs:
        spec.channel_specs = [
            ChannelSpecLfFemSingle(),
            ChannelSpecOpxPlusSingle()
        ]

    for channel_spec in spec.channel_specs:
        channel_templates = spec.get_channel_template_from_spec(channel_spec)
        if assign_channels_to_spec(spec, instruments, channel_templates, same_con=True, same_slot=True):
            return

    raise WirerException(spec)


def allocate_rf_channels(spec: WiringSpec, instruments: Instruments):
    """
    Try to allocate RF channels to a MW-FEM. If that doesn't work, look for a
    combination of LF-FEM I/Q and Octave channels, or OPX+ I/Q and Octave
    channels.
    """
    if not spec.channel_specs:
        spec.channel_specs = [
            ChannelSpecMwFemSingle(),
            ChannelSpecLfFemBaseband() & ChannelSpecOctave(),
            ChannelSpecOpxPlusBaseband() & ChannelSpecOctave(),
        ]

    for channel_spec in spec.channel_specs:
        channel_templates = spec.get_channel_template_from_spec(channel_spec)
        if assign_channels_to_spec(spec, instruments, channel_templates, same_con=True, same_slot=True):
            return

    raise WirerException(spec)
