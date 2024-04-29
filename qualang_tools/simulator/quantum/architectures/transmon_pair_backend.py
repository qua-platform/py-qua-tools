import numpy as np
from qiskit_dynamics import Solver, DynamicsBackend

from .backend_options import dt, solver_options
from .operators import dim, ident
from .transmon_pair_settings import TransmonPairSettings
from .transmon_pair import TransmonPair


class TransmonPairBackend(DynamicsBackend):
    def __init__(self, transmon_pair_settings: TransmonPairSettings, **options):
        transmon_pair = TransmonPair(transmon_pair_settings)

        transmon_1_drive_operator = np.kron(ident, transmon_pair.transmon_1.drive_operator())
        transmon_2_drive_operator = np.kron(transmon_pair.transmon_2.drive_operator(), ident)

        solver = Solver(
            static_hamiltonian=transmon_pair.system_hamiltonian(),
            hamiltonian_operators=[transmon_1_drive_operator,
                                   transmon_2_drive_operator,
                                   transmon_1_drive_operator,
                                   transmon_2_drive_operator],
            rotating_frame=transmon_pair.system_hamiltonian(),
            hamiltonian_channels=["d0", "d1", "u0", "u1"],
            channel_carrier_freqs={"d0": transmon_pair.transmon_1.resonant_frequency,
                                   "d1": transmon_pair.transmon_2.resonant_frequency,
                                   "u0": transmon_pair.transmon_2.resonant_frequency,
                                   "u1": transmon_pair.transmon_1.resonant_frequency},
            dt=dt,
            array_library="jax",
        )

        # Consistent solver option to use throughout notebook
        options = {**solver_options, **options}

        super().__init__(solver=solver, subsystem_dims=[dim, dim], solver_options=options)