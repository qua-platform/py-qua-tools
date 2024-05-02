from typing import Dict, List

from qualang_tools.simulator.quantum.architectures.transmon_pair_backend_from_qua import ConfigToTransmonPairBackendMap
from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines.timelines import Timeline


Element = str
ElementToTimelineMap = Dict[Element, List[Timeline]]


class Context:
    def __init__(self, qua_config: dict):
        self.vars = {}
        self.qua_config: dict = qua_config
        self.timelines: ElementToTimelineMap = {}

    def create_timelines_for_each_element(self, channel_map: ConfigToTransmonPairBackendMap):
        for element, channel in channel_map.items():
            self.timelines[element] = [
                Timeline(
                    qubit_index=channel.qubit_index,
                    pulse_channel=channel.get_qiskit_pulse_channel()
                )
            ]
