from typing import Dict, List, Union

from .channel_spec import ChannelSpec
from .element import Element, ElementId, QubitReference, QubitPairReference
from .types import QubitsType, QubitPairsType
from .wiring_spec import WiringSpec, WiringFrequency, WiringIOType, WiringLineType


class ConnectivityBase:
    """
    The base class for managing quantum element wiring configurations.

    This class serves as the foundation for storing and managing placeholders for
    quantum elements (such as qubits and qubit pairs) and their associated wiring
    specifications. It tracks each element's unique ID and the specific wiring
    configurations required to integrate those elements into a quantum setup.

    The wiring specifications include details such as:
    - Frequency at which the element is driven (e.g., RF or DC).
    - Input/output requirements for the element (e.g., input, output, or both).
    - The specific line type (e.g., resonator, drive, flux) for the element.
    - Any constraints on the channels (e.g., frequency, module location, etc.).
    - The associated high-level quantum components (e.g., qubits, resonators, etc.).

    Attributes:
        elements (Dict[ElementId, Element]): A dictionary mapping each element's
                                              unique ID to its corresponding `Element` object.
        specs (List[WiringSpec]): A list of all the wiring specifications (placeholders)
                                  added for the quantum elements.
    """

    def __init__(self):
        """
        Initializes a new `ConnectivityBase` instance with empty storage for elements
        and wiring specifications.

        This constructor sets up two primary containers:
        - `self.elements`: A dictionary that holds the quantum elements (e.g., qubits).
        - `self.specs`: A list that stores wiring specifications that detail how
                        the quantum elements are connected and configured.
        """
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
        """
        Adds wiring specifications (placeholders) for quantum elements.

        This method allows the addition of one or more wiring specifications for
        a set of quantum elements. Each specification defines the configuration of
        how the element will be wired, including frequency, input/output lines,
        line type, triggering conditions, and channel constraints. The specifications
        serve as placeholders, and no channels are actually allocated at this stage.

        Args:
            frequency (WiringFrequency): The frequency at which the element will be driven (e.g., RF or DC).
            io_type (WiringIOType): The input/output configuration for the element (e.g., input, output, or both).
            line_type (Union[WiringLineType, str]): The type of line for the wiring (e.g., resonator, drive, flux).
            triggered (bool): Whether the wiring is triggered (e.g., by an external event).
            constraints (ChannelSpec): Any channel constraints that should be applied (e.g., frequency domain,
                                       slot availability, etc.).
            elements (List[Element]): The quantum elements to which the wiring specifications apply.
            shared_line (bool, optional): Whether the wiring specification should apply to a shared line
                                          (defaults to False).

        Returns:
            List[WiringSpec]: A list of the generated wiring specifications for the provided elements.
        """
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
        """
        Creates `Element` objects for a list of qubits.

        This method constructs `Element` objects for each qubit reference in the provided `qubits` list
        and adds them to the internal `self.elements` dictionary. If the element for a qubit already exists,
        it will not be recreated.

        Args:
            qubits (QubitsType): A list or a single qubit reference to generate element objects for.

        Returns:
            List[Element]: A list of `Element` objects created or retrieved for the specified qubits.
        """
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
        """
        Creates `Element` objects for a list of qubit pairs.

        This method constructs `Element` objects for each qubit pair reference in the provided `qubit_pairs` list
        and adds them to the internal `self.elements` dictionary. If the element for a qubit pair already exists,
        it will not be recreated.

        Args:
            qubit_pairs (QubitPairsType): A list or a single qubit pair reference to generate element objects for.

        Returns:
            List[Element]: A list of `Element` objects created or retrieved for the specified qubit pairs.
        """
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
        """
        Adds multiple `Element` objects to the internal storage.

        This method adds a list of `Element` objects to the internal `self.elements` dictionary.

        Args:
            elements (List[Element]): A list of `Element` objects to add to the internal storage.
        """
        for element in elements:
            self._add_element(element)

    def _add_element(self, element: Element):
        """
        Adds a single `Element` object to the internal storage.

        This method adds a single `Element` object to the internal `self.elements` dictionary, using
        the element's unique ID as the key.

        Args:
            element (Element): The `Element` object to add to the internal storage.
        """
        self.elements[element.id] = element
