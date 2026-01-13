from qualang_tools.wirer.connectivity.channel_spec import ChannelSpec
from qualang_tools.wirer.connectivity.types import QubitsType, QubitPairsType, ElementsType
from qualang_tools.wirer.connectivity.wiring_spec import WiringFrequency, WiringIOType, WiringLineType
from qualang_tools.wirer.connectivity.connectivity_base import ConnectivityBase


class ConnectivityQuantumDotQubits(ConnectivityBase):
    """
    Represents the high-level wiring configuration for a quantum-dot-based QPU setup.

    This class defines and stores placeholders for quantum elements (e.g., quantum dots, sensor dots, and resonators)
    and specifies the wiring requirements for each of their control and readout lines. It enables
    the configuration of line types (e.g., drive, plunger gates, barrier gates, sensor gates), their I/O roles,
    and associated frequency domains (RF or DC), as well as constraints for channel allocation.

    The API is designed to model quantum dot configurations, including voltage gates for charge control,
    RF drive lines for quantum dot manipulation, and resonator lines for readout via sensor dots.
    """

    def add_voltage_gate_lines(self, voltage_gates: ElementsType, triggered: bool = False,
                               constraints: ChannelSpec = None, name: str = 'vg',
                               wiring_line_type: WiringLineType = WiringLineType.GLOBAL_GATE) -> None:
        """
        Adds specifications (placeholders) for generic voltage gate lines.

        This is a generic method for adding voltage gate lines with a specified line type. It can be used
        to add any type of voltage gate (global gates, sensor gates, etc.) by specifying the `wiring_line_type`.
        For more specific use cases, consider using the dedicated methods:
        - `add_quantum_dot_voltage_gate_lines`: For plunger gates on quantum dots
        - `add_quantum_dot_pair_voltage_gate_lines`: For barrier gates on quantum dot pairs
        - `add_sensor_dot_voltage_gate_lines`: For sensor gates on sensor dots

        No channels are allocated at this stage.

        Args:
            voltage_gates (ElementsType): The voltage gate elements to configure. Can be a single element ID
                or a list of element IDs.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.
            name (str, optional): Name prefix for the elements. Defaults to 'vg'.
            wiring_line_type (WiringLineType, optional): The type of wiring line (e.g., GLOBAL_GATE, SENSOR_GATE).
                Defaults to GLOBAL_GATE.
        """
        elements = self._add_named_elements(name, voltage_gates)
        self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, wiring_line_type, triggered, constraints, elements
        )

    def add_sensor_dots(self, sensor_dots: ElementsType, triggered: bool = False, constraints: ChannelSpec = None,
                        shared_resonator_line: bool = False, resonator_wiring_frequency=WiringFrequency.DC) -> None:
        """
        Adds specifications (placeholders) for sensor dots, including both voltage gate lines and resonator lines.

        This method is a convenience function that adds both the voltage gate lines and resonator lines for sensor dots.
        It calls `add_sensor_dot_voltage_gate_lines` and `add_sensor_dot_resonator_line` internally.

        No channels are allocated at this stage.

        Args:
            sensor_dots (ElementsType): The sensor dot elements to configure. Can be a single element ID
                or a list of element IDs.
            triggered (bool, optional): Whether the lines are triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channels, if any. Defaults to None.
            shared_resonator_line (bool, optional): Whether multiple sensor dots share the same resonator line.
                Defaults to False.
            resonator_wiring_frequency (WiringFrequency, optional): The frequency domain for the resonator line.
                Defaults to DC (for LF-FEM, typical for tank circuits below 800MHz). Use RF for MW-FEM
                (only for resonators above 2GHz).
        """
        self.add_sensor_dot_voltage_gate_lines(sensor_dots, triggered=triggered, constraints=constraints)
        self.add_sensor_dot_resonator_line(sensor_dots, triggered=triggered, constraints=constraints, shared_line=shared_resonator_line, wiring_frequency=resonator_wiring_frequency)

    def add_sensor_dot_voltage_gate_lines(self, sensor_dots: ElementsType, triggered: bool = False, constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for voltage gate lines on sensor dots.

        This method configures sensor gate line specifications (placeholders) for sensor dots, which are
        used for charge sensing in quantum dot systems. The gates are configured as SENSOR_GATE line type.

        No channels are allocated at this stage.

        Args:
            sensor_dots (ElementsType): The sensor dot elements to configure. Can be a single element ID
                or a list of element IDs.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.
        """
        self.add_voltage_gate_lines(sensor_dots, triggered=triggered, constraints=constraints, name='s',
                                    wiring_line_type=WiringLineType.SENSOR_GATE)

    def add_quantum_dots(self, quantum_dots: QubitsType):
        """
        Adds specifications (placeholders) for quantum dots, including voltage gate lines and drive lines.

        This method is a convenience function that adds both the plunger gate lines and RF drive lines for
        quantum dots. It calls `add_quantum_dot_voltage_gate_lines` and `add_quantum_dot_drive_lines` internally.

        No channels are allocated at this stage.

        Args:
            quantum_dots (QubitsType): The quantum dots to configure. Can be a single quantum dot ID or a list of quantum dot IDs.
        """
        self.add_quantum_dot_voltage_gate_lines(quantum_dots)
        self.add_quantum_dot_drive_lines(quantum_dots)

    def add_quantum_dot_pairs(self, quantum_dot_pairs: QubitPairsType, triggered: bool = False, constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for quantum dot pairs, including barrier gate lines.

        This method configures barrier gate line specifications (placeholders) for pairs of quantum dots, which are
        used to control the barrier between quantum dots in a pair. It calls `add_quantum_dot_pair_voltage_gate_lines`
        internally.

        No channels are allocated at this stage.

        Args:
            quantum_dot_pairs (QubitPairsType): The quantum dot pairs to configure. Can be a single pair (tuple of two quantum dot IDs)
                or a list of pairs.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.
        """
        self.add_barrier_voltage_gate_lines(quantum_dot_pairs, triggered=triggered, constraints=constraints)

    def add_sensor_dot_resonator_line(self, sensor_dots, triggered: bool = False, constraints: ChannelSpec = None,
                                      shared_line: bool = False, wiring_frequency=WiringFrequency.DC):
        """
        Adds a specification (placeholder) for a resonator line for sensor dots.

        This method configures a resonator line specification (placeholder) for sensor dots, typically used
        for readout via tank circuits. The default frequency is DC (LF-FEM) since most tank circuits operate
        below 800MHz and connect to LF-FEM. Only resonators above 2GHz can connect to MW-FEM due to bandwidth
        limitations. If you need to connect to MW-FEM, explicitly set `wiring_frequency=WiringFrequency.RF`.

        No channels are allocated at this stage.

        Args:
            sensor_dots: The sensor dot elements to associate with the resonator line. Can be a single element ID
                or a list of element IDs.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.
            shared_line (bool, optional): Whether multiple sensor dots share the same resonator line.
                Defaults to False.
            wiring_frequency (WiringFrequency, optional): The frequency domain for the resonator line.
                Defaults to DC (for LF-FEM, typical for tank circuits below 800MHz). Use RF for MW-FEM
                (only for resonators above 2GHz).

        Returns:
            List[WiringSpec]: A list of wiring specifications (placeholders) for the resonator lines.
        """
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

    def add_quantum_dot_drive_lines(self, quantum_dots: QubitsType, triggered: bool = False,
                                          constraints: ChannelSpec = None, wiring_frequency=WiringFrequency.RF, shared_line=False):
        """
        Adds specifications (placeholders) for RF drive lines for quantum dots.

        This method configures the drive line specifications (placeholders) for quantum dots,
        which are typically used to apply RF control signals for quantum dot manipulation. It allows optional
        triggering and constraints on which channel configurations can be allocated for this line.

        No channels are allocated at this stage.

        Args:
            quantum_dots (QubitsType): The quantum dots to configure the drive lines for. Can be a single quantum dot ID
                or a list of quantum dot IDs.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.
            wiring_frequency (WiringFrequency, optional): The frequency domain for the drive line.
                Defaults to RF.
            shared_line (bool, optional): Whether multiple quantum dots share the same drive line.
                Defaults to False.

        Returns:
            List[WiringSpec]: A list of wiring specifications (placeholders) for the quantum dot drive lines.
        """
        elements = self._make_qubit_elements(quantum_dots)
        return self.add_wiring_spec(
            wiring_frequency, WiringIOType.OUTPUT, WiringLineType.DRIVE, triggered, constraints, elements, shared_line=shared_line,
        )

    def add_quantum_dot_voltage_gate_lines(self, quantum_dots: QubitsType, triggered: bool = False,
                                     constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for plunger gate lines on quantum dots.

        This method configures plunger gate line specifications (placeholders) for quantum dots.
        Plunger gates are used to control the charge occupation of quantum dots, allowing manipulation
        of the quantum dot state. The gates are configured as PLUNGER_GATE line type with DC frequency.

        This is distinct from `add_voltage_gate_lines` which is a generic method. Use this method when
        you specifically need plunger gates for quantum dots.

        No channels are allocated at this stage.

        Args:
            quantum_dots (QubitsType): The quantum dots to configure the plunger gate lines for. Can be a single quantum dot ID
                or a list of quantum dot IDs.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            List[WiringSpec]: A list of wiring specifications (placeholders) for the plunger gate lines.
        """
        elements = self._make_qubit_elements(quantum_dots)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.PLUNGER_GATE, triggered, constraints, elements
        )

    def add_barrier_voltage_gate_lines(self, quantum_dot_pairs: QubitPairsType, triggered: bool = False,
                                          constraints: ChannelSpec = None):
        """
        Adds specifications (placeholders) for barrier gate lines on quantum dot pairs.

        This method configures barrier gate line specifications (placeholders) for pairs of quantum dots.
        Barrier gates are used to control the tunnel coupling between quantum dots in a pair, enabling
        two-quantum-dot operations. The gates are configured as BARRIER_GATE line type with DC frequency.

        This is distinct from `add_voltage_gate_lines` which is a generic method. Use this method when
        you specifically need barrier gates for quantum dot pairs.

        No channels are allocated at this stage.

        Args:
            quantum_dot_pairs (QubitPairsType): The quantum dot pairs to configure the barrier gate lines for. Can be a single
                pair (tuple of two quantum dot IDs) or a list of pairs.
            triggered (bool, optional): Whether the line is triggered. Defaults to False.
            constraints (ChannelSpec, optional): Constraints on the channel, if any. Defaults to None.

        Returns:
            List[WiringSpec]: A list of wiring specifications (placeholders) for the barrier gate lines.
        """
        elements = self._make_qubit_pair_elements(quantum_dot_pairs)
        return self.add_wiring_spec(
            WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.BARRIER_GATE, triggered, constraints, elements
        )
