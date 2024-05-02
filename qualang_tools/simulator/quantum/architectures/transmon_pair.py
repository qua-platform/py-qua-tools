import numpy as np

from .operators import a0, a0dag, a1, a1dag, ident
from .transmon import Transmon
from .transmon_pair_settings import TransmonPairSettings


class TransmonPair:
    def __init__(self, settings: TransmonPairSettings):
        self.transmon_1 = Transmon(settings.transmon_1_settings)
        self.transmon_2 = Transmon(settings.transmon_2_settings)
        self.coupling_strength = settings.coupling_strength

    def system_hamiltonian(self) -> np.ndarray:
        transmon_1_system_hamiltonian = np.kron(ident, self.transmon_1.system_hamiltonian())
        transmon_2_system_hamiltonian = np.kron(self.transmon_2.system_hamiltonian(), ident)
        interaction_hamiltonian = self._interaction_hamiltonian()

        return transmon_1_system_hamiltonian + transmon_2_system_hamiltonian + interaction_hamiltonian

    def _interaction_hamiltonian(self) -> np.ndarray:
        return 2 * np.pi * self.coupling_strength * ((a0 + a0dag) @ (a1 + a1dag))

    def transmon_1_drive_operator(self, quadrature="I"):
        return np.kron(ident, self.transmon_1.drive_operator(quadrature))

    def transmon_2_drive_operator(self, quadrature="I"):
        return np.kron(self.transmon_2.drive_operator(quadrature), ident)

