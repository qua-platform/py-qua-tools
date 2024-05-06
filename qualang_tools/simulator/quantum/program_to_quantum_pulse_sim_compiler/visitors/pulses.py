from typing import Union, List, Tuple

import numpy as np
from qiskit import pulse
from qiskit.pulse.library import Pulse

from qualang_tools.simulator.quantum.program_ast.measure import Measure
from qualang_tools.simulator.quantum.program_ast.play import Play


Length = int
IQShapes = List[Pulse]


def waveform_shape(node: Union[Play, Measure],
                   config: dict,
                   length: int = None,
                   amplitude_scale_factor: float = None) -> Tuple[Length, IQShapes]:
    pulse_name = config['elements'][node.element]['operations'][node.operation]
    pulse = config['pulses'][pulse_name]
    if length is None:
        length = pulse['length']

    length *= 4  # from clock-cycles to ns
    waveforms = pulse['waveforms']

    if set(waveforms.keys()) != {'I', 'Q'}:
        raise NotImplementedError()

    I = config['waveforms'][waveforms['I']]
    Q = config['waveforms'][waveforms['Q']]

    I_Q_shapes = []
    for waveform_config in [I, Q]:
        if waveform_config['type'] == 'constant':
            I_Q_shapes.append(_construct_constant_pulse(waveform_config, length, amplitude_scale_factor))
        elif waveform_config['type'] == 'arbitrary':
            I_Q_shapes.append(_construct_arbitrary_pulse(waveform_config, length, amplitude_scale_factor))
        else:
            raise NotImplementedError()

    return length, I_Q_shapes


def _construct_constant_pulse(waveform_config: dict, length: int, amplitude_scale_factor=None) -> Pulse:
    amplitude = waveform_config["sample"]
    if amplitude_scale_factor is not None:
        amplitude *= amplitude_scale_factor

    return pulse.library.Constant(length, amplitude)


def _construct_arbitrary_pulse(waveform_config: dict, length: int, amplitude_scale_factor=None) -> Pulse:
    amplitudes = np.array(waveform_config["samples"])
    if amplitude_scale_factor is not None:
        amplitudes *= amplitude_scale_factor

    if length != len(amplitudes):
        if length == len(amplitudes) * 4:
            # todo: do this for any integer N, not just N=4
            amplitudes = np.repeat(amplitudes, 4)
        else:
            raise NotImplementedError("Interpolation not yet implemented.")

    return pulse.library.Waveform(amplitudes, limit_amplitude=False)
