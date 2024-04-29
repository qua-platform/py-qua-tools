from typing import Union

from qualang_tools.simulator.quantum.program_ast.measure import Measure
from qualang_tools.simulator.quantum.program_ast.play import Play


def lookup_pulse_parameters(node: Union[Play, Measure], config) -> tuple[int, float, float]:
    pulse_name = config['elements'][node.element]['operations'][node.operation]
    pulse = config['pulses'][pulse_name]
    length = pulse['length']

    waveforms = pulse['waveforms']

    if set(waveforms.keys()) != {'I', 'Q'}:
        raise NotImplementedError()

    I = config['waveforms'][waveforms['I']]
    Q = config['waveforms'][waveforms['Q']]

    if I['type'] != "constant":
        raise NotImplementedError()
    if Q['type'] != "constant":
        raise NotImplementedError()

    return length, I["sample"], Q["sample"]
