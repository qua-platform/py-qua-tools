from typing import Dict

from qiskit_dynamics import Solver, DynamicsBackend

from .backend_options import dt, solver_options
from .from_qua_channels import TransmonPairBackendChannel, TransmonPairBackendChannelReadout, \
    TransmonPairBackendChannelIQ, ChannelType
from .operators import dim
from .transmon_pair import TransmonPair

Element = str
ConfigToTransmonPairBackendMap = Dict[Element, TransmonPairBackendChannel]


class TransmonPairBackendFromQUA(DynamicsBackend):
    def __init__(self,
                 transmon_pair: TransmonPair,
                 config_to_backend_map: ConfigToTransmonPairBackendMap,
                 **options):
        self.transmon_pair = transmon_pair
        self.config_to_backend_map = config_to_backend_map
        solver = self._solver_from_map()
        options = {**solver_options, **options}

        super().__init__(solver=solver, subsystem_dims=[dim, dim], solver_options=options)

    def _solver_from_map(self):
        hamiltonian_operators = []
        hamiltonian_channels = []
        channel_carrier_freqs = {}
        qubit_to_drive_channel_map = {}

        drive_index = -1
        control_index = -1
        for element, channel in self.config_to_backend_map.items():
            if isinstance(channel, TransmonPairBackendChannelIQ):
                for quadrature, operator in zip("IQ", [channel.operator_i, channel.operator_q]):
                    if channel.type == ChannelType.DRIVE:
                        drive_index += 1
                        index = drive_index
                    elif channel.type == ChannelType.CONTROL:
                        control_index += 1
                        index = control_index
                    else:
                        raise NotImplementedError(f"Unrecognized channel type {channel.type}")
                    hamiltonian_operators.append(operator)
                    channel_name = channel.type.value + str(index)
                    hamiltonian_channels.append(channel_name)
                    channel_carrier_freqs[channel_name] = channel.carrier_frequency
                    qubit_to_drive_channel_map[channel.qubit_index] = index
                    channel.assign_channel_index(index, quadrature=quadrature)

            elif isinstance(channel, TransmonPairBackendChannelReadout):
                channel.assign_channel_index(qubit_to_drive_channel_map[channel.qubit_index])

            else:
                raise NotImplementedError()

        solver = Solver(
            static_hamiltonian=self.transmon_pair.system_hamiltonian(),
            hamiltonian_operators=hamiltonian_operators,
            rotating_frame=self.transmon_pair.system_hamiltonian(),
            hamiltonian_channels=hamiltonian_channels,
            channel_carrier_freqs=channel_carrier_freqs,
            dt=dt,
            array_library="jax",
        )

        return solver
