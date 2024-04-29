from typing import Dict, List

from qualang_tools.simulator.quantum.program_to_quantum_pulse_sim_compiler.timelines import Timeline


class Context:
    def __init__(self, config: dict, ):
        self.vars = {}
        self.config = config
        self.timelines: Dict[str, List[Timeline]] = {}
        self._ended = True

        elements = config['elements']
        for element in elements:
            self.timelines[element] = [Timeline(0, 0)]
