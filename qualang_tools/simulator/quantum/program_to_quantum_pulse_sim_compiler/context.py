from typing import Dict, List

from qualang_tools.simulator.quantum.architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import Timeline


class Context:
    def __init__(self, config: dict, map: ConfigToTransmonPairBackendMap):
        self.vars = {}
        self.config = config
        self.timelines: Dict[str, List[Timeline]] = {}
        self._ended = True

        for element, channel in map.items():
            self.timelines[element] = [Timeline(channel.qubit_index, channel.get_channel_index())]
