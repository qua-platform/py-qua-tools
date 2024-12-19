from qualang_tools.wirer.connectivity.channel_spec import ChannelSpec
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannel,
    InstrumentChannelLfFemInput,
    InstrumentChannelLfFemOutput,
    InstrumentChannelMwFemInput,
    InstrumentChannelMwFemOutput,
    InstrumentChannelOpxPlusInput,
    InstrumentChannelOpxPlusOutput,
    InstrumentChannelOctaveInput,
    InstrumentChannelOctaveOutput,
    InstrumentChannelExternalMixerInput,
    InstrumentChannelExternalMixerOutput,
    InstrumentChannelOpxPlusDigitalOutput,
    InstrumentChannelMwFemDigitalOutput,
    InstrumentChannelLfFemDigitalOutput,
    InstrumentChannelOctaveDigitalInput,
    InstrumentChannelExternalMixerDigitalInput
)

# A channel template is a partially filled InstrumentChannel object
ChannelTemplate = InstrumentChannel


class ChannelSpecMwFemSingle(ChannelSpec):
    def __init__(self, con: int = None, slot: int = None, in_port: int = None, out_port: int = None):

        super().__init__()
        self.channel_templates = [
            InstrumentChannelMwFemInput(con=con, slot=slot, port=in_port),
            InstrumentChannelMwFemOutput(con=con, slot=slot, port=out_port),
        ]


class ChannelSpecLfFemSingle(ChannelSpec):
    def __init__(
        self, con: int = None, in_slot: int = None, in_port: int = None, out_slot: int = None, out_port: int = None
    ):

        super().__init__()
        self.channel_templates = [
            InstrumentChannelLfFemInput(con=con, slot=in_slot, port=in_port),
            InstrumentChannelLfFemOutput(con=con, slot=out_slot, port=out_port),
        ]


class ChannelSpecLfFemBaseband(ChannelSpec):
    def __init__(
        self,
        con: int = None,
        slot: int = None,
        in_port_i: int = None,
        in_port_q: int = None,
        out_port_i: int = None,
        out_port_q: int = None,
    ):

        super().__init__()
        self.channel_templates = [
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_i),
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_q),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_i),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_q),
        ]


class ChannelSpecOpxPlusSingle(ChannelSpec):
    def __init__(self, con: int = None, in_port: int = None, out_port: int = None):

        super().__init__()
        self.channel_templates = [
            InstrumentChannelOpxPlusInput(con=con, port=in_port),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port),
        ]


class ChannelSpecOpxPlusBaseband(ChannelSpec):
    def __init__(
        self,
        con: int = None,
        in_port_i: int = None,
        in_port_q: int = None,
        out_port_i: int = None,
        out_port_q: int = None,
    ):

        super().__init__()
        self.channel_templates = [
            InstrumentChannelOpxPlusInput(con=con, port=in_port_i),
            InstrumentChannelOpxPlusInput(con=con, port=in_port_q),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_i),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_q),
        ]


class ChannelSpecOctave(ChannelSpec):
    def __init__(self, index: int = None, rf_in: int = None, rf_out: int = None):
        super().__init__()
        self.channel_templates = [
            InstrumentChannelOctaveInput(con=index, port=rf_in),
            InstrumentChannelOctaveOutput(con=index, port=rf_out),
        ]


class ChannelSpecExternalMixer(ChannelSpec):
    def __init__(self, index: int = None, rf_in: int = None, rf_out: int = None):
        super().__init__()
        self.channel_templates = [
            InstrumentChannelExternalMixerInput(con=index, port=rf_in),
            InstrumentChannelExternalMixerOutput(con=index, port=rf_out),
        ]


class ChannelSpecLfFemBasebandAndOctave(ChannelSpec):
    def __init__(
            self,
            con: int = None,
            slot: int = None,
            in_port_i: int = None,
            in_port_q: int = None,
            out_port_i: int = None,
            out_port_q: int = None,
            octave_index: int = None,
            rf_in: int = None,
            rf_out: int = None,
    ):
        super().__init__()
        self.channel_templates = [
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_i),
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_q),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_i),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_q),
            InstrumentChannelOctaveInput(con=octave_index, port=rf_in),
            InstrumentChannelOctaveOutput(con=octave_index, port=rf_out),
        ]

class ChannelSpecLfFemBasebandAndExternalMixer(ChannelSpec):
    def __init__(
        self,
        con: int = None,
        slot: int = None,
        in_port_i: int = None,
        in_port_q: int = None,
        out_port_i: int = None,
        out_port_q: int = None,
        mixer_index: int = None,
    ):
        super().__init__()
        self.channel_templates = [
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_i),
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_q),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_i),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_q),
            InstrumentChannelExternalMixerInput(con=mixer_index, port=1),
            InstrumentChannelExternalMixerOutput(con=mixer_index, port=1),
        ]


class ChannelSpecOpxPlusBasebandAndOctave(ChannelSpec):
    def __init__(
            self,
            con: int = None,
            in_port_i: int = None,
            in_port_q: int = None,
            out_port_i: int = None,
            out_port_q: int = None,
            octave_index: int = None,
            rf_in: int = None,
            rf_out: int = None,
    ):
        super().__init__()
        self.channel_templates = [
            InstrumentChannelOpxPlusInput(con=con, port=in_port_i),
            InstrumentChannelOpxPlusInput(con=con, port=in_port_q),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_i),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_q),
            InstrumentChannelOctaveInput(con=octave_index, port=rf_in),
            InstrumentChannelOctaveOutput(con=octave_index, port=rf_out),
        ]

class ChannelSpecOpxPlusBasebandAndExternalMixer(ChannelSpec):
    def __init__(
        self,
        con: int = None,
        in_port_i: int = None,
        in_port_q: int = None,
        out_port_i: int = None,
        out_port_q: int = None,
        mixer_index: int = None,
    ):
        super().__init__()
        self.channel_templates = [
            InstrumentChannelOpxPlusInput(con=con, port=in_port_i),
            InstrumentChannelOpxPlusInput(con=con, port=in_port_q),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_i),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_q),
            InstrumentChannelExternalMixerInput(con=mixer_index, port=1),
            InstrumentChannelExternalMixerOutput(con=mixer_index, port=1),
        ]


class ChannelSpecOpxPlusDigital(ChannelSpec):
    def __init__(self, con: int = None, out_port: int = None):
        super().__init__()
        self.channel_templates = [InstrumentChannelOpxPlusDigitalOutput(con=con, port=out_port)]


class ChannelSpecMwFemDigital(ChannelSpec):
    def __init__(self, con: int = None, out_port: int = None):
        super().__init__()
        self.channel_templates = [InstrumentChannelMwFemDigitalOutput(con=con, port=out_port)]


class ChannelSpecLfFemDigital(ChannelSpec):
    def __init__(self, con: int = None, out_port: int = None):
        super().__init__()
        self.channel_templates = [InstrumentChannelLfFemDigitalOutput(con=con, port=out_port)]


class ChannelSpecOctaveDigital(ChannelSpec):
    def __init__(self, con: int = None, in_port: int = None):
        super().__init__()
        self.channel_templates = [InstrumentChannelOctaveDigitalInput(con=con, port=in_port)]


class ChannelSpecExternalMixerDigital(ChannelSpec):
    def __init__(self, con: int = None, in_port: int = None):
        super().__init__()
        self.channel_templates = [InstrumentChannelExternalMixerDigitalInput(con=con, port=in_port)]


mw_fem_spec = ChannelSpecMwFemSingle
lf_fem_spec = ChannelSpecLfFemSingle
lf_fem_iq_spec = ChannelSpecLfFemBaseband
lf_fem_iq_octave_spec = ChannelSpecLfFemBasebandAndOctave
lf_fem_iq_ext_mixer_spec = ChannelSpecLfFemBasebandAndExternalMixer
opx_spec = ChannelSpecOpxPlusSingle
opx_iq_spec = ChannelSpecOpxPlusBaseband
opx_iq_octave_spec = ChannelSpecOpxPlusBasebandAndOctave
opx_iq_ext_mixer_spec = ChannelSpecOpxPlusBasebandAndExternalMixer
octave_spec = ChannelSpecOctave
ext_mixer_spec = ChannelSpecExternalMixer
opx_dig_spec = ChannelSpecOpxPlusDigital
