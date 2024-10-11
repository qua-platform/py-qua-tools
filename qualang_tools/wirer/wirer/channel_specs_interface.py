from .channel_specs import (
    ChannelSpecMwFemSingle,
    ChannelSpecLfFemSingle,
    ChannelSpecLfFemBaseband,
    ChannelSpecLfFemBasebandAndOctave,
    ChannelSpecOpxPlusSingle,
    ChannelSpecOpxPlusBaseband,
    ChannelSpecOpxPlusBasebandAndOctave,
    ChannelSpecOctave,
)

mw_fem_spec = ChannelSpecMwFemSingle
lf_fem_spec = ChannelSpecLfFemSingle
lf_fem_iq_spec = ChannelSpecLfFemBaseband
lf_fem_iq_octave_spec = ChannelSpecLfFemBasebandAndOctave
opx_spec = ChannelSpecOpxPlusSingle
opx_iq_spec = ChannelSpecOpxPlusBaseband
opx_iq_octave_spec = ChannelSpecOpxPlusBasebandAndOctave
octave_spec = ChannelSpecOctave
