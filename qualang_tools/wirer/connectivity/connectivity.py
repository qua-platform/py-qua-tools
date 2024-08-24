import copy
from typing import Dict, List

from .channel_spec import ChannelSpec
from .element import Element, ElementId, QubitReference, QubitPairReference
from .types import QubitsType, QubitPairsType
from .wiring_spec import WiringSpec, WiringFrequency, WiringIOType, WiringLineType


class Connectivity:
    """
    This class stores placeholders for the quantum elements which will be used
    in a setup, as well as the wiring specification for each of those elements.
    This includes at what frequency the element will be driven, whether it
    requires input/output or both lines, if it is required on a particular
    module or FEM slot, and what high-level component will be manipulated.
    """

    def __init__(self):
        self.elements: Dict[ElementId, Element] = {}
        self.specs: List[WiringSpec] = []

    def add_fixed_transmons(self, qubits: QubitsType):
        self.add_resonator_line(qubits)
        self.add_qubit_drive_lines(qubits)

    def add_flux_tunable_transmons(self, qubits: QubitsType):
        self.add_resonator_line(qubits)
        self.add_qubit_drive_lines(qubits)
        self.add_qubit_flux_lines(qubits)

    def add_resonator_line(self, qubits: QubitsType, channel_spec: ChannelSpec = None):
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(WiringFrequency.RF, WiringIOType.INPUT_AND_OUTPUT, WiringLineType.RESONATOR, channel_spec, elements, shared_line=True)

    def add_qubit_drive_lines(self, qubits: QubitsType, channel_spec: ChannelSpec = None):
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(WiringFrequency.RF, WiringIOType.OUTPUT, WiringLineType.DRIVE, channel_spec, elements)

    def add_qubit_flux_lines(self, qubits: QubitsType, channel_spec: ChannelSpec = None):
        elements = self._make_qubit_elements(qubits)
        return self.add_wiring_spec(WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.FLUX, channel_spec, elements)

    def add_qubit_pair_flux_lines(self, qubit_pairs: QubitPairsType, channel_spec: ChannelSpec = None):
        elements = self._make_qubit_pair_elements(qubit_pairs)
        return self.add_wiring_spec(WiringFrequency.DC, WiringIOType.OUTPUT, WiringLineType.COUPLER, channel_spec, elements)

    def add_wiring_spec(self, frequency: WiringFrequency, io_type: WiringIOType, line_type: WiringLineType,
                        channel_spec: ChannelSpec, elements: List[Element], shared_line: bool = False, ):
        specs = []
        if shared_line:
            spec = WiringSpec(frequency, io_type, line_type, channel_spec, elements)
            specs.append(spec)
        else:
            for element in elements:
                spec = WiringSpec(frequency, io_type, line_type, channel_spec, element)
                specs.append(spec)
        self.specs.extend(specs)

        return specs

    def _make_qubit_elements(self, qubits: QubitsType):
        if not isinstance(qubits, list):
            qubits = [qubits]

        elements = []
        for qubit in qubits:
            id = QubitReference(qubit)
            if id not in self.elements:
                self.elements[id] = Element(id)
            elements.append(self.elements[id])

        return elements

    def _make_qubit_pair_elements(self, qubit_pairs: QubitPairsType):
        if not isinstance(qubit_pairs, list):
            qubit_pairs = [qubit_pairs]

        elements = []
        for qubit_pair in qubit_pairs:
            id = QubitPairReference(*qubit_pair)
            if id not in self.elements:
                self.elements[id] = Element(id)
            elements.append(self.elements[id])

        return elements
