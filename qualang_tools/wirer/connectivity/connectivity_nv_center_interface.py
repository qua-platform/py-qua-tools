from qualang_tools.wirer.connectivity.channel_spec import ChannelSpec
from qualang_tools.wirer.connectivity.types import QubitsType
from qualang_tools.wirer.connectivity.wiring_spec import WiringFrequency, WiringIOType, WiringLineType
from qualang_tools.wirer.connectivity.connectivity_base import ConnectivityBase
from qualang_tools.wirer.instruments.instrument_channel import (
    InstrumentChannelLfFemOutput,
    InstrumentChannelLfFemDigitalOutput,
)


class ConnectivityNVCenters(ConnectivityBase):
    """
    Represents the high-level wiring configuration for an NV center-based QPU setup.

    This class defines and stores placeholders for quantum elements (e.g., qubits and lasers)
    and specifies the wiring requirements for each of their control and readout lines. It enables
    the configuration of line types (e.g., drive, laser, readout), their I/O roles, and associated
    frequency domains (RF or DC), as well as constraints for channel allocation.

    The API is designed to model single NV centers, along with pairwise coupling mechanisms.
    """

    def add_nv_center(self, qubits: QubitsType):
        """
        Adds specifications (placeholders) for nv centers.

        This method configures the wiring specifications (placeholders) for a set of nv centers,
        including the qubit drive and laser. No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to configure for nv centers.
        """
        self.add_laser(qubits)
        self.add_spcm(qubits)
        self.add_qubit_drive(qubits)

    def add_laser(self, qubits: QubitsType, triggered: bool = True, constraints: ChannelSpec = None):
        """
        Adds a specification (placeholder) for a laser for the specified qubits.

        This method configures a laser specification (placeholder) that can handle output,
        typically for reading out and initializing the state of qubits. It also allows optional
        triggering and constraints on which channel configurations can be allocated.

        No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to associate with the laser.
            triggered (bool, optional): Whether the laser is triggered. Defaults to True.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the laser.
        """
        elements = self._make_qubit_elements(qubits)

        # check constraints to assign correct wiring frequency
        if constraints and constraints.channel_templates:
            channel_types = {type(ch) for ch in constraints.channel_templates}
            if InstrumentChannelLfFemOutput in channel_types:
                wiring_freq = WiringFrequency.DC
            elif InstrumentChannelLfFemDigitalOutput in channel_types:
                wiring_freq = WiringFrequency.DO
            else:
                raise ValueError("Invalid channel constraint.")
        else:
            wiring_freq = WiringFrequency.DC

        return self.add_wiring_spec(
            wiring_freq,
            WiringIOType.OUTPUT,
            WiringLineType.LASER,
            triggered,
            constraints,
            elements,
        )

    def add_spcm(self, qubits: QubitsType, triggered: bool = False, constraints: ChannelSpec = None):
        """
        Adds a specification (placeholder) for a spcm for the specified qubits.

        This method configures a spcm specification (placeholder) that can handle input,
        typically for reading out the state of qubits. It also allows optional
        triggering and constraints on which channel configurations can be allocated.

        No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to associate with the laser.
            triggered (bool, optional): Whether the readout is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the spcm.
        """
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.DC,
            WiringIOType.INPUT,
            WiringLineType.SPCM,
            triggered,
            constraints,
            elements,
        )

    def add_qubit_drive(self, qubits: QubitsType, triggered: bool = False, constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for drive lines for the specified qubits.

        This method configures the qubit drive line specifications (placeholders), which are typically used to apply
        control signals to qubits. It allows optional triggering and constraints on which channel configurations
        can be allocated for this line.

        No channels are allocated at this stage.


        Args:
            qubits (QubitsType): The qubits to configure the drive lines for.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the qubit drive lines.
        """
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.RF,
            WiringIOType.OUTPUT,
            WiringLineType.DRIVE,
            triggered,
            constraints,
            elements,
        )
