from enum import Enum

from qualang_tools.wirer.connectivity.channel_spec import ChannelSpec
from qualang_tools.wirer.connectivity.types import QubitsType, QubitPairsType, ElementsType
from qualang_tools.wirer.connectivity.wiring_spec import WiringFrequency, WiringIOType, WiringLineType
from qualang_tools.wirer.connectivity.connectivity_base import ConnectivityBase


class ConnectivityQuantumDotQubits(ConnectivityBase):
    """
    Represents the high-level wiring configuration for a quantum-dot-based QPU setup.

    This class defines and stores placeholders for quantum elements (e.g., qubits and resonators)
    and specifies the wiring requirements for each of their control and readout lines. It enables
    the configuration of line types (e.g., drive, flux, resonator), their I/O roles, and associated
    frequency domains (RF or DC), as well as constraints for channel allocation.

    The API is designed to model a variety of qubit configurations, such as fixed-frequency and
    flux-tunable transmons, along with pairwise coupling mechanisms like cross-resonance and ZZ drive.
    """

    def add_voltage_gate_lines(self, voltage_gates: ElementsType, triggered: bool = False,
                               constraints: ChannelSpec = None, name: str = 'vg',
                               wiring_line_type: WiringLineType = WiringLineType.GLOBAL_GATE) -> None:
        elements = self._add_named_elements(name, voltage_gates)
        self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, wiring_line_type, triggered, constraints, elements
        )

    def add_sensor_dots(self, sensor_dots: ElementsType, triggered: bool = False, constraints: ChannelSpec = None,
                        shared_resonator_line: bool = False) -> None:
        self.add_voltage_gate_lines(sensor_dots, triggered=triggered, constraints=constraints, name='s',
                                    wiring_line_type=WiringLineType.SENSOR_GATE)
        self.add_sensor_dot_voltage_gate_lines(sensor_dots, triggered=triggered, constraints=constraints,)

    def add_sensor_dot_voltage_gate_lines(self, sensor_dots: ElementsType, triggered: bool = False, constraints: ChannelSpec = None):
        self.add_voltage_gate_lines(sensor_dots, triggered=triggered, constraints=constraints, name='s',
                                    wiring_line_type=WiringLineType.SENSOR_GATE)

    def add_qubits(self, qubits: QubitsType):
        self.add_qubit_voltage_gate_lines(qubits)
        self.add_quantum_dot_qubit_drive_lines(qubits)

    def add_qubit_pairs(self, qubit_pairs: QubitPairsType, triggered: bool = False, constraints: ChannelSpec = None):
        self.add_qubit_pair_voltage_gate_lines(qubit_pairs, triggered=triggered, constraints=constraints)

    def add_sensor_dot_resonator_line(self, sensor_dots, triggered: bool = False, constraints: ChannelSpec = None,
                                      shared_line: bool = False, wiring_frequency=WiringFrequency.RF):
        elements = self._add_named_elements('s', sensor_dots)
        return self.add_wiring_spec(
            wiring_frequency,
            WiringIOType.INPUT_AND_OUTPUT,
            WiringLineType.RF_RESONATOR,
            triggered,
            constraints,
            elements,
            shared_line=shared_line,
        )

    def add_quantum_dot_qubit_drive_lines(self, qubits: QubitsType, triggered: bool = False,
                                          constraints: ChannelSpec = None, wiring_frequency=WiringFrequency.RF):
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            wiring_frequency, WiringIOType.OUTPUT, WiringLineType.DRIVE, triggered, constraints, elements
        )

    def add_qubit_voltage_gate_lines(self, qubits: QubitsType, triggered: bool = False,
                                     constraints: ChannelSpec = None):
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.PLUNGER_GATE, triggered, constraints, elements
        )

    def add_qubit_pair_voltage_gate_lines(self, qubit_pairs: QubitPairsType, triggered: bool = False,
                                          constraints: ChannelSpec = None):
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.BARRIER_GATE, triggered, constraints, elements
        )
