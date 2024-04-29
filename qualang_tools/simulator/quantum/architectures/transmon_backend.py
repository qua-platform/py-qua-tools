from qiskit_dynamics import Solver, DynamicsBackend

from .backend_options import solver_options, dt
from .operators import dim
from .transmon_settings import TransmonSettings
from .transmon import Transmon


class TransmonBackend(DynamicsBackend):
    def __init__(self, transmon_settings: TransmonSettings, **options):
        transmon = Transmon(transmon_settings)

        solver = Solver(
            static_hamiltonian=transmon.system_hamiltonian(),
            hamiltonian_operators=[transmon.drive_operator()],
            rotating_frame=transmon.system_hamiltonian(),
            hamiltonian_channels=["d0"],
            channel_carrier_freqs={"d0": transmon.resonant_frequency},
            dt=dt,
            array_library="jax",
        )

        # Consistent solver option to use throughout notebook
        options = {**solver_options, **options}
        super().__init__(solver=solver, subsystem_dims=[dim], solver_options=options)