from .channel_spec import ChannelSpec
from .types import QubitsType, QubitPairsType
from .wiring_spec import WiringFrequency, WiringIOType, WiringLineType
from .connectivity_base import ConnectivityBase


class Connectivity(ConnectivityBase):
    def add_fixed_transmons(self, qubits: QubitsType):
        self.add_resonator_line(qubits)
        self.add_qubit_drive_lines(qubits)

    def add_flux_tunable_transmons(self, qubits: QubitsType):
        self.add_resonator_line(qubits)
        self.add_qubit_drive_lines(qubits)
        self.add_qubit_flux_lines(qubits)

    def add_resonator_line(self, qubits: QubitsType, triggered: bool = False, constraints: ChannelSpec = None):
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
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.RF, WiringIOType.OUTPUT, WiringLineType.DRIVE, triggered, constraints, elements
        )

    def add_qubit_charge_lines(self, qubits: QubitsType, constraints: ChannelSpec = None):
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.CHARGE, False, constraints, elements
        )

    def add_qubit_flux_lines(self, qubits: QubitsType, constraints: ChannelSpec = None):
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.FLUX, False, constraints, elements
        )

    def add_qubit_pair_flux_lines(self, qubit_pairs: QubitPairsType, constraints: ChannelSpec = None):
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.COUPLER, False, constraints, elements
        )

    def add_qubit_pair_cross_resonance_lines(
        self, qubit_pairs: QubitPairsType, triggered: bool = False, constraints: ChannelSpec = None
    ):
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(
            WiringFrequency.RF, WiringIOType.OUTPUT, WiringLineType.CROSS_RESONANCE, triggered, constraints, elements
        )

    def add_qubit_pair_zz_drive_lines(
        self, qubit_pairs: QubitPairsType, triggered: bool = False, constraints: ChannelSpec = None
    ):
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(
            WiringFrequency.RF, WiringIOType.OUTPUT, WiringLineType.ZZ_DRIVE, triggered, constraints, elements
        )
