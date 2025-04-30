from .channel_spec import ChannelSpec
from .types import QubitsType, QubitPairsType
from .wiring_spec import WiringFrequency, WiringIOType, WiringLineType
from .connectivity_base import ConnectivityBase


class Connectivity(ConnectivityBase):
    """
    Represents the high-level wiring configuration for a transmon-based QPU setup.

    This class defines and stores placeholders for quantum elements (e.g., qubits and resonators) 
    and specifies the wiring requirements for each of their control and readout lines. It enables 
    the configuration of line types (e.g., drive, flux, resonator), their I/O roles, and associated 
    frequency domains (RF or DC), as well as constraints for channel allocation.

    The API is designed to model a variety of qubit configurations, such as fixed-frequency and 
    flux-tunable transmons, along with pairwise coupling mechanisms like cross-resonance and ZZ drive.
    """

    def add_fixed_transmons(self, qubits: QubitsType):
        """
        Adds specifications (placeholders) for resonator and drive lines for fixed-frequency transmons.

        This method configures the wiring specifications (placeholders) for a set of fixed-frequency transmons, 
        including the resonator and qubit drive lines. No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to configure for fixed-frequency transmons.
        """
        self.add_resonator_line(qubits)
        self.add_qubit_drive_lines(qubits)

    def add_flux_tunable_transmons(self, qubits: QubitsType):
        """
        Adds specifications (placeholders) for resonator, drive, and flux lines for flux-tunable transmons.

        This method configures the wiring specifications (placeholders) for flux-tunable transmons, including 
        resonator, qubit drive, and flux bias lines. No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to configure for flux-tunable transmons.
        """
        self.add_resonator_line(qubits)
        self.add_qubit_drive_lines(qubits)
        self.add_qubit_flux_lines(qubits)

    def add_resonator_line(self, qubits: QubitsType, triggered: bool = False, constraints: ChannelSpec = None):
        """
        Adds a specification (placeholder) for a resonator line for the specified qubits.

        This method configures a resonator line specification (placeholder) that can handle both input and output, 
        typically for reading out the state of qubits. It also allows optional triggering and constraints on
        which channel configurations can be allocated for this line.

        No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to associate with the resonator line.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the resonator line.
        """
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.RF,
            WiringIOType.INPUT_AND_OUTPUT,
            WiringLineType.RESONATOR,
            triggered,
            constraints,
            elements,
            shared_line=True,
        )

    def add_qubit_drive_lines(self, qubits: QubitsType, triggered: bool = False, constraints: ChannelSpec = None):
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
            WiringFrequency.RF, WiringIOType.OUTPUT, WiringLineType.DRIVE, triggered, constraints, elements
        )

    def add_qubit_charge_lines(self, qubits: QubitsType, constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for charge lines for the specified qubits.

        This method configures charge line specifications (placeholders) for qubits, typically used for DC control.
        One can also specify constraints on which channel configurations can be allocated for this line.

        No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to configure the charge lines for.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the qubit charge lines.
        """
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.CHARGE, False, constraints, elements
        )

    def add_qubit_flux_lines(self, qubits: QubitsType, constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for flux bias lines for the specified qubits.

        This method configures flux bias line specifications (placeholders), typically used for DC control, to tune 
        the qubits' frequency. One can also specify constraints on which channel configurations can be allocated
        for this line.

        No channels are allocated at this stage.

        Args:
            qubits (QubitsType): The qubits to configure the flux bias lines for.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the qubit flux bias lines.
        """
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.FLUX, False, constraints, elements
        )

    def add_qubit_pair_flux_lines(self, qubit_pairs: QubitPairsType, constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for flux lines for a pair of qubits.

        This method configures flux line specifications (placeholders), typically for controlling couplers or other 
        interactions between qubit pairs. One can also specify constraints on which channel configurations can
        be allocated for this line.

        No channels are allocated at this stage.

        Args:
            qubit_pairs (QubitPairsType): The qubit pairs to configure the flux lines for.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the qubit pair flux lines.
        """
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.COUPLER, False, constraints, elements
        )

    def add_qubit_pair_cross_resonance_lines(
        self, qubit_pairs: QubitPairsType, triggered: bool = False, constraints: ChannelSpec = None
    ):
        """
        Adds specifications (placeholders) for cross-resonance drive lines for a pair of qubits.

        This method configures cross-resonance line specifications (placeholders) for two qubits, 
        typically used to implement two-qubit gate operations. One can also specify constraints on which
        channel configurations can be allocated for this line.

        No channels are allocated at this stage.

        Args:
            qubit_pairs (QubitPairsType): The qubit pairs to configure the cross-resonance lines for.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the cross-resonance drive lines.
        """
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(
            WiringFrequency.RF, WiringIOType.OUTPUT, WiringLineType.CROSS_RESONANCE, triggered, constraints, elements
        )

    def add_qubit_pair_zz_drive_lines(
        self, qubit_pairs: QubitPairsType, triggered: bool = False, constraints: ChannelSpec = None
    ):
        """
        Adds specifications (placeholders) for ZZ drive lines for a pair of qubits.

        This method configures ZZ drive line specifications (placeholders) for two qubits, typically used 
        for two-qubit gate operations, in the RF frequency domain. One can also specify constraints on which
        channel configurations can be allocated for this line.

        No channels are allocated at this stage.

        Args:
            qubit_pairs (QubitPairsType): The qubit pairs to configure the ZZ drive lines for.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            A wiring specification (placeholder) for the ZZ drive lines.
        """
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(
            WiringFrequency.RF, WiringIOType.OUTPUT, WiringLineType.ZZ_DRIVE, triggered, constraints, elements
        )
