from qiskit_dynamics import DynamicsBackend
from qm import Program

from qualang_tools.simulator.quantum import Compiler
from qualang_tools.simulator.quantum.architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap


def simulate(qua_program: Program,
             qua_config: dict,
             qua_config_to_backend_map: ConfigToTransmonPairBackendMap,
             backend: DynamicsBackend,
             num_shots: int):

    compiler = Compiler(config=qua_config)
    sim = compiler.compile(qua_program, qua_config_to_backend_map, backend)

    results = sim.run(num_shots=num_shots)

    return results
