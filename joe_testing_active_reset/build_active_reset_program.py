import numpy as np
Amp = 0.5

config = {
    'version': 1,

    'controllers': {
        'con1': {
            'type': 'opx1',
            'analog_outputs': {
                1: {'offset': +0.0},
                2: {'offset': +0.0},
                3: {'offset': +0.0},
                4: {'offset': +0.0},
            },
            'digital_outputs': {
                1: {},
            },
            'analog_inputs': {
                1: {'offset': +0.0},
                2: {'offset': +0.0},
            }
        }
    },

    'elements': {
        'qubit': {
            'mixInputs': {
                'I': ('con1', 1),
                'Q': ('con1', 2),
                'lo_frequency': 5.10e9,
                'mixer': 'mixer_qubit'
            },
            'intermediate_frequency': 5.15e6,
            'operations': {
                'gauss_pulse': 'gauss_pulse_in'
            },
        },
        'resonator': {
            'mixInputs': {
                'I': ('con1', 3),
                'Q': ('con1', 4),
                'lo_frequency': 6.00e9,
                'mixer': 'mixer_res'
            },
            'intermediate_frequency': 6.12e6,
            'operations': {
                'readout': 'meas_pulse_in',
            },
            'time_of_flight': 180,
            'smearing': 0,
            'outputs': {
                'out1': ('con1', 1),
                'out2': ('con1', 2)
            }

        },
    },

    'pulses': {
        'meas_pulse_in': {
            'operation': 'measurement',
            'length': 20,
            'waveforms': {
                'I': 'exc_wf',
                'Q': 'zero_wf'
            },
            'integration_weights': {
                'cos': 'cos',
                'sin': 'sin',
                'minus_sin': 'minus_sin',
            },
            'digital_marker': 'marker1'
        },
        'gauss_pulse_in': {
            'operation': 'control',
            'length': 20,
            'waveforms': {
                'I': 'gauss_wf',
                'Q': 'zero_wf'
            },
        }
    },

    'waveforms': {
        'exc_wf': {
                'type': 'constant',
                'sample': 0.479
        },
        'zero_wf': {
            'type': 'constant',
            'sample': 0.0
        },
        'gauss_wf': {
            'type': 'arbitrary',
            'samples': [0.005, 0.013,
                        0.02935, 0.05899883936462147,
                        0.10732436763802927, 0.1767030571463228,
                        0.2633180579359862, 0.35514694106994277,
                        0.43353720001453067, 0.479, 0.479,
                        0.4335372000145308, 0.3551469410699429,
                        0.26331805793598645, 0.17670305714632292,
                        0.10732436763802936, 0.05899883936462152,
                        0.029354822126316085, 0.01321923408389493,
                        0.005387955348880817]
        }
    },

    'digital_waveforms': {
        'marker1': {
            'samples': [(1, 4), (0, 2), (1, 1), (1, 0)]
        }
    },

    'integration_weights': {
        'cos': {
            'cosine': [(4.0,20)],
            'sine': [(0.0,20)]
        },
        'sin': {
            'cosine': [(0.0,20)],
            'sine': [(4.0,20)]
        },
        'minus_sin': {
            'cosine': [(0.0,20)],
            'sine': [(-4.0,20)]
        },
    },

    'mixers': {
        'mixer_res': [
            {'intermediate_frequency': 6.12e6, 'lo_freq': 6.00e9, 'correction': [1.0, 0.0, 0.0, 1.0]}
        ],
        'mixer_qubit': [
            {'intermediate_frequency': 5.15e6, 'lo_freq': 5.10e9, 'correction': [1.0, 0.0, 0.0, 1.0]}
        ],
    }
}

gaus_pulse_len = 20 # nsec
gaus_arg = np.linspace(-3, 3, gaus_pulse_len)
gaus_wf = np.exp(-gaus_arg**2/2)
gaus_wf = Amp * gaus_wf / np.max(gaus_wf)




from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager

qmm = QuantumMachinesManager()

qm = qmm.open_qm(config)
