from typing import Dict, List, Union

from .channel_spec import ChannelSpec
from .element import Element, ElementId, QubitReference, QubitPairReference
from .types import QubitsType, QubitPairsType
from .wiring_spec import WiringSpec, WiringFrequency, WiringIOType, WiringLineType


class ConnectivityBase:
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

    def add_wiring_spec(
        self,
        frequency: WiringFrequency,
        io_type: WiringIOType,
        line_type: Union[WiringLineType, str],
        triggered: bool,
        constraints: ChannelSpec,
        elements: List[Element],
        shared_line: bool = False,
    ):
        specs = []
        for element in elements:
            if element.id not in self.elements:
                self._add_element(element)

        if shared_line:
            spec = WiringSpec(frequency, io_type, line_type, triggered, constraints, elements)
            specs.append(spec)
        else:
            for element in elements:
                spec = WiringSpec(frequency, io_type, line_type, triggered, constraints, element)
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

    def _add_elements(self, elements: List[Element]):
        for element in elements:
            self._add_element(element)

    def _add_element(self, element: Element):
        self.elements[element.id] = element
