import numpy as np
from .operators import N, ident, a, adag
from .transmon_settings import TransmonSettings


class Transmon:
    def __init__(self, settings: TransmonSettings):
        self.settings = settings
        self.resonant_frequency = settings.resonant_frequency
        self.rabi_frequency = settings.rabi_frequency
        self.anharmonicity = settings.anharmonicity

    def system_hamiltonian(self) -> np.ndarray:
        return 2 * np.pi * self.resonant_frequency * N + np.pi * self.anharmonicity * N * (N - ident)

    def drive_operator(self) -> np.ndarray:
        return 2 * np.pi * self.rabi_frequency * (a + adag)
