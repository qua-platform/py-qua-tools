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
    InstrumentChannelExternalMixerDigitalInput,
)

# A channel template is a partially filled InstrumentChannel object
ChannelTemplate = InstrumentChannel


class ChannelSpecMwFemSingle(ChannelSpec):
    def __init__(self, con: int = None, slot: int = None, in_port: int = None, out_port: int = None):
        """
        Represents a single-channel specification for Microwave Front-End Module (MW-FEM).

        If specified, any of the provided arguments can be used to constrain the configuration of a
        single MW-FEM channel. If no arguments are provided, the configuration is unconstrained.

        For example, if the argument slot=2 is specified, then this specification can ONLY be
        satisfied by an available MW-FEM installed in slot 2 of an OPX1000 chassis.

        Attributes:
            channel_templates (list): A list containing initialized
                InstrumentChannelMwFemInput and InstrumentChannelMwFemOutput objects.

        Args:
            con (int, optional): Controller identifier for both input and output channels (any positive integer).
            slot (int, optional): FEM slot identifier for both input and output channels (1–8).
            in_port (int, optional): Input port identifier (1–2).
            out_port (int, optional): Output port identifier (1–8).
        """

        super().__init__()
        self.channel_templates = [
            InstrumentChannelMwFemInput(con=con, slot=slot, port=in_port),
            InstrumentChannelMwFemOutput(con=con, slot=slot, port=out_port),
        ]


class ChannelSpecLfFemSingle(ChannelSpec):
    def __init__(
        self, con: int = None, in_slot: int = None, in_port: int = None, out_slot: int = None, out_port: int = None
    ):
        """
        Represents a single-channel specification for Low-Frequency Front-End Module (LF-FEM).

        If specified, any of the provided arguments can be used to constrain the configuration of a
        single LF-FEM channel. If no arguments are provided, the configuration is unconstrained.

        For example, if in_slot=3 is specified AND this specification is used later to allocate an input
        channel, then it should ONLY be satisfied by an LF-FEM (with a free input channel) installed in
        slot 3 of an OPX1000 chassis. If unspecified, it can be satisfied by an LF-FEM installed on any
        given slot.

        Attributes:
            channel_templates (list): A list containing initialized
                InstrumentChannelLfFemInput and InstrumentChannelLfFemOutput objects.

        Args:
            con (int, optional): Controller identifier common to both input and output channels (any positive integer).
            in_slot (int, optional): Slot index for the input channel (1–8; only relevant if allocating input).
            in_port (int, optional): Port index for the input channel (1–2; only relevant if allocating input).
            out_slot (int, optional): Slot index for the output channel (1–8; only relevant if allocating output).
            out_port (int, optional): Port index for the output channel (1–8; only relevant if allocating output).
        """
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
        """
        Represents a baseband (unmixed) I/Q channel specification for LF-FEM.

        If specified, any of the provided arguments can be used to constrain the configuration of a
        baseband I/Q LF-FEM channel group. If no arguments are provided, the configuration is unconstrained.

        For example, if in_port_q=2 is specified AND this specification is later used to allocate an
        input Q-quadrature channel, then it should ONLY be satisfied by an LF-FEM with its Q input on port 2.
        If unspecified, it can be satisfied by any available port on the FEM.

        Attributes:
            channel_templates (list): Two LF-FEM input and two LF-FEM output channels for I and Q.

        Args:
            con (int, optional): Controller identifier (any positive integer).
            slot (int, optional): Slot index shared by all four I/Q channels (1–8).
            in_port_i (int, optional): Port index for the I input channel (1–2; only relevant if allocating input).
            in_port_q (int, optional): Port index for the Q input channel (1–2; only relevant if allocating input).
            out_port_i (int, optional): Port index for the I output channel (1–8; only relevant if allocating output).
            out_port_q (int, optional): Port index for the Q output channel (1–8; only relevant if allocating output).
        """
        super().__init__()
        self.channel_templates = [
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_i),
            InstrumentChannelLfFemInput(con=con, slot=slot, port=in_port_q),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_i),
            InstrumentChannelLfFemOutput(con=con, slot=slot, port=out_port_q),
        ]


class ChannelSpecOpxPlusSingle(ChannelSpec):
    def __init__(self, con: int = None, in_port: int = None, out_port: int = None):
        """
        Represents a single-channel specification for OPX+.

        If specified, any of the provided arguments can be used to constrain the configuration of an
        OPX+ channel. If no arguments are provided, the configuration is unconstrained.

        For example, if out_port=1 is specified AND this specification is used to allocate an output
        channel, then it should ONLY be satisfied by an OPX+ with output port 1 available. If unspecified,
        then the specification can be satisfied by any available port.

        Attributes:
           channel_templates (list): One OPX+ input and one OPX+ output channel.

        Args:
           con (int, optional): Controller (OPX+) identifier (any positive integer).
           in_port (int, optional): Port index for input (1-2; only relevant if allocating input).
           out_port (int, optional): Port index for output (1-10; only relevant if allocating output).
        """
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
        """
        Represents a baseband (unmixed) I/Q channel specification for OPX+.

        If specified, any of the provided arguments can be used to constrain the configuration of a
        baseband I/Q OPX+ channel group. If no arguments are provided, the configuration is unconstrained.

        For example, if out_port_i=1 is specified AND this specification is later used to allocate an
        I-quadrature output channel, then it should ONLY be satisfied by an OPX+ with output port 1 available.

        Attributes:
            channel_templates (list): I/Q-paired OPX+ input and output channels.

        Args:
            con (int, optional): Controller identifier.
            in_port_i (int, optional): Input port index for I (1-2; only relevant if allocating input).
            in_port_q (int, optional): Input port index for Q (1-2; only relevant if allocating input).
            out_port_i (int, optional): Output port index for I (1-10; only relevant if allocating output).
            out_port_q (int, optional): Output port index for Q (1-10; only relevant if allocating output).
        """
        super().__init__()
        self.channel_templates = [
            InstrumentChannelOpxPlusInput(con=con, port=in_port_i),
            InstrumentChannelOpxPlusInput(con=con, port=in_port_q),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_i),
            InstrumentChannelOpxPlusOutput(con=con, port=out_port_q),
        ]


class ChannelSpecOctave(ChannelSpec):
    def __init__(self, index: int = None, rf_in: int = None, rf_out: int = None):
        """
        Represents an RF channel specification for an Octave module.

        If specified, any of the provided arguments can be used to constrain the configuration of an
        Octave RF channel. If no arguments are provided, the configuration is unconstrained.

        For example, if rf_out=1 is specified AND this specification is used to allocate an output channel,
        then it should ONLY be satisfied by an Octave with RF output port 1 available.

        Attributes:
            channel_templates (list): One Octave input and one Octave output channel.

        Args:
            index (int, optional): Octave module identifier (any positive integer).
            rf_in (int, optional): RF input port index (1-2; only relevant if allocating input).
            rf_out (int, optional): RF output port index (1-5; only relevant if allocating output).
        """
        super().__init__()
        self.channel_templates = [
            InstrumentChannelOctaveInput(con=index, port=rf_in),
            InstrumentChannelOctaveOutput(con=index, port=rf_out),
        ]


class ChannelSpecExternalMixer(ChannelSpec):
    def __init__(self, index: int = None, rf_in: int = None, rf_out: int = None):
        """
        Represents an RF channel specification for an External Mixer.

        If specified, any of the provided arguments can be used to constrain the configuration of a
        single RF channel. If no arguments are provided, the configuration is unconstrained.

        For example, if rf_out=0 is specified AND this specification is used to allocate an output
        channel, then it should ONLY be satisfied by an External Mixer with RF output port 0 available.

        Args:
            index (int, optional): External mixer identifier.
            rf_in (int, optional): Input RF port (only relevant if allocating input).
            rf_out (int, optional): Output RF port (only relevant if allocating output).
        """

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
        """
        Represents a combined baseband I/Q + RF specification for LF-FEM and Octave.

        If specified, any of the provided arguments can be used to constrain the configuration of a
        baseband I/Q and RF channel pair. If no arguments are provided, the configuration is unconstrained.

        For example, if rf_in=2 is specified AND this specification is used to allocate an input RF channel,
        then it should ONLY be satisfied by an Octave with input port 2 available. If it is unspecified,
        then the rf input channel can be satisfied by any available port.

        Note that if you only need input, then the `out` specifications will be ignored and vice versa.

        Args:
            con (int, optional): Controller identifier for the LF-FEM (any positive integer).
            slot (int, optional): Slot index shared by the I/Q baseband channels (1-8).
            in_port_i (int, optional): I input port index (1-2; only relevant if allocating input).
            in_port_q (int, optional): Q input port index (1-2; only relevant if allocating input).
            out_port_i (int, optional): I output port index (1-8; only relevant if allocating output).
            out_port_q (int, optional): Q output port index (1-8; only relevant if allocating output).
            octave_index (int, optional): Octave module index (any positive integer).
            rf_in (int, optional): RF input port (1-2; only relevant if allocating input).
            rf_out (int, optional): RF output port (1-5; only relevant if allocating output).
        """
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
        """
        Represents a combined baseband I/Q + RF specification for LF-FEM and External mixer.

        If specified, any of the provided arguments can be used to constrain the configuration of a
        baseband I/Q and External mixer RF channel pair. If no arguments are provided, the configuration is unconstrained.

        For example, if mixer_index=1 is specified AND this specification is used to allocate an RF
        channel, then it should ONLY be satisfied by an external mixer with index 1. Otherwise, it can
        be satisfied by any available external mixer.

        Args:
            con (int, optional): Controller identifier for the LF-FEM (any positive integer).
            slot (int, optional): Slot index for the LF-FEM (1-8).
            in_port_i (int, optional): I input port index (1-2; only relevant if allocating input).
            in_port_q (int, optional): Q input port index (1-2; only relevant if allocating input).
            out_port_i (int, optional): I output port index (1-8; only relevant if allocating output).
            out_port_q (int, optional): Q output port index (1-8; only relevant if allocating output).
            mixer_index (int, optional): External mixer index.
        """
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
        """
        Represents a combined baseband I/Q + RF specification for OPX+ and Octave.

        If specified, any of the provided arguments can be used to constrain the configuration of a
        baseband I/Q and RF channel pair. If no arguments are provided, the configuration is unconstrained.

        For example, if out_port_q=3 is specified AND this specification is used to allocate the Q output,
        then it should ONLY be satisfied by an OPX+ with Q output port 3.

        Args:
            con (int, optional): Controller identifier for the OPX+ (any positive integer).
            in_port_i (int, optional): I input port index (1-2; only relevant if allocating input).
            in_port_q (int, optional): Q input port index (1-2; only relevant if allocating input).
            out_port_i (int, optional): I output port index (1-10; only relevant if allocating output).
            out_port_q (int, optional): Q output port index (1-10; only relevant if allocating output).
            octave_index (int, optional): Octave module index (any positive integer).
            rf_in (int, optional): RF input port (1-2; only relevant if allocating input).
            rf_out (int, optional): RF output port (1-5; only relevant if allocating output).
        """
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
        """
        Represents a combined baseband I/Q + RF specification for OPX+ and External mixer.

        If specified, any of the provided arguments can be used to constrain the configuration of a
        baseband I/Q and External mixer RF channel pair. If no arguments are provided, the configuration is unconstrained.

        For example, if mixer_index=0 is specified, then it should ONLY be satisfied by an External mixer
        with index 0 during allocation.

        Args:
            con (int, optional): Controller identifier for the OPX+ (any positive integer).
            in_port_i (int, optional): I input port index (1-2; only relevant if allocating input).
            in_port_q (int, optional): Q input port index (1-2; only relevant if allocating input).
            out_port_i (int, optional): I output port index (1-10; only relevant if allocating output).
            out_port_q (int, optional): Q output port index (1-10; only relevant if allocating output).
            mixer_index (int, optional): External mixer index.
        """

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
        """
        Represents a digital output specification for OPX+.

        If specified, the arguments constrain the configuration of a digital output channel.
        If no arguments are provided, the configuration is unconstrained.

        For example, if out_port=6 is specified, then it should ONLY be satisfied by an OPX+
        digital output port 6. Otherwise, any available OPX+ digital output port can be selected.

        Args:
            con (int, optional): Controller identifier for the OPX+ (any positive integer).
            out_port (int, optional): Digital output port index (1-10).
        """
        super().__init__()
        self.channel_templates = [InstrumentChannelOpxPlusDigitalOutput(con=con, port=out_port)]


class ChannelSpecMwFemDigital(ChannelSpec):
    def __init__(self, con: int = None, slot: int = None, out_port: int = None):
        """
        Represents a digital output specification for MW-FEM.

        If specified, the arguments constrain the configuration of a digital output channel.
        If no arguments are provided, the configuration is unconstrained.

        For example, if con=2 is specified, then it should ONLY be satisfied by the MW-FEM controller
        with index 2. Otherwise, any available MW-FEM controller can be used.

        Args:
            con (int, optional): Controller identifier for the OPX1000
            slot (int, optional): FEM slot identifier for the MW-FEM (1–8).
            out_port (int, optional): Digital output port index (1-8).
        """
        super().__init__()
        self.channel_templates = [InstrumentChannelMwFemDigitalOutput(con=con, slot=slot, port=out_port)]


class ChannelSpecLfFemDigital(ChannelSpec):
    def __init__(self, con: int = None, slot: int = None, out_port: int = None):
        """
        Represents a digital output specification for LF-FEM.

        If specified, the arguments constrain the configuration of a digital output channel.
        If no arguments are provided, the configuration is unconstrained.

        For example, if out_port=0 is specified, then it should ONLY be satisfied by the LF-FEM
        digital output port 0. Otherwise, any available port may be selected.

        Args:
            con (int, optional): Controller identifier for the OPX1000.
            slot (int, optional): FEM slot inside the chassis for the LF-FEM (1–8).
            out_port (int, optional): Digital output port index.
        """
        super().__init__()
        self.channel_templates = [InstrumentChannelLfFemDigitalOutput(con=con, slot=slot, port=out_port)]


class ChannelSpecOctaveDigital(ChannelSpec):
    def __init__(self, con: int = None, in_port: int = None):
        """
        Represents a digital input specification for an Octave module.

        If specified, the arguments constrain the configuration of a digital input channel.
        If no arguments are provided, the configuration is unconstrained.

        For example, if in_port=4 is specified, then it should ONLY be satisfied by an Octave
        digital input port 4. Otherwise, any available Octave input port may be used.

        Args:
            con (int, optional): Controller identifier for the Octave module.
            in_port (int, optional): Digital input port index.
        """
        super().__init__()
        self.channel_templates = [InstrumentChannelOctaveDigitalInput(con=con, port=in_port)]


class ChannelSpecExternalMixerDigital(ChannelSpec):
    def __init__(self, con: int = None, in_port: int = None):
        """
        Represents a digital input specification for an External mixer.

        If specified, the arguments constrain the configuration of a digital input channel.
        If no arguments are provided, the configuration is unconstrained.

        For example, if con=1 is specified, then it should ONLY be satisfied by the External mixer
        controller with index 1. Otherwise, any available mixer can satisfy the specification.

        Args:
            con (int, optional): Controller identifier for the External mixer.
            in_port (int, optional): Digital input port index.
        """
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
