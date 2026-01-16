from .connectivity_transmon_interface import ConnectivitySuperconductingQubits
from .connectivity_nv_center_interface import ConnectivityNVCenters
from .connectivity_quantum_dot_interface import ConnectivityQuantumDotQubits


class Connectivity(ConnectivitySuperconductingQubits, ConnectivityNVCenters, ConnectivityQuantumDotQubits):
    """
    Represents the high-level wiring configuration for the supported QPU setups: superconducting qubits, NV centers, and quantum dots.

    This class defines and stores placeholders for quantum elements (e.g., qubits and resonators)
    and specifies the wiring requirements for each of their control and readout lines. It enables
    the configuration of line types (e.g., drive, flux, resonator), their I/O roles, and associated
    frequency domains (RF or DC), as well as constraints for channel allocation.

    The API is designed to model a variety of qubit configurations, such as fixed-frequency and
    flux-tunable transmons, NV centers, and quantum dots, along with pairwise coupling mechanisms
    like cross-resonance and ZZ drive.
    """

    pass
