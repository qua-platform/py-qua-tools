LO_freq = 2.87e9
NV_IF = 30e6
NV1_conditional_freq = 29.8e6
NV2_conditional_freq = 29.9e6


pi_length = 56
ent_len=32
red_length = 16
pi_amplitude = 0.3
pi_amplitude2 = pi_amplitude / ((pi_length - 2) / pi_length)

init_len = 9000
readout_len = 10000

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "type": "opx1",
            "analog_outputs": {i + 1: {"offset": 0.0} for i in range(10)},
            "digital_outputs": {
                1: {},
                2: {},
                3: {},
                4: {},
                5: {},
                6: {},
            },
            "analog_inputs": {
                1: {"offset": 0.0},
                2: {"offset": 0.0},
            },
        },
    },
    "elements": {
        "qubit1": {
            "mixInputs": {
                "I": ("con1", 1),
                "Q": ("con1", 2),
                "lo_frequency": LO_freq,
            },
            "digitalInputs": {
                "laser_green": {"buffer": 0, "delay": 0, "port": ("con1", 1)},
            },
            "outputs": {"out1": ("con1", 1)},
            # "hold_offset": {"duration": 16},
            "time_of_flight": 28,
            "smearing": 0,
            "intermediate_frequency": NV_IF,
            "operations": {
                "pi": "pi",
                "pi_plus_2ns_wait": "pi_2ns",
                "pi_half": "pi_half",
                "readout": "readout",
                "laser": "laser_on",
                "SSRO_readout": "readout_red",
            },
        },
        "qubit2": {
            "mixInputs": {
                "I": ("con1", 3),
                "Q": ("con1", 4),
                "lo_frequency": LO_freq,
            },
            "digitalInputs": {
                "laser_green": {"buffer": 0, "delay": 0, "port": ("con1", 3)},
            },
            "outputs": {"out1": ("con1", 2)},
            "time_of_flight": 28,
            "smearing": 0,
            "intermediate_frequency": NV_IF,
            "operations": {
                "pi": "pi",
                "pi_plus_2ns_wait": "pi_2ns",
                "pi_half": "pi_half",
                "readout": "readout",
                "laser": "laser_on",
                "SSRO_readout": "readout_red",
            },
        },
        "qubit3": {
            "singleInput": {"port": ("con1", 5)},
            "intermediate_frequency": 2e6,
            "operations": {
                "pi": "pi_single",
            },
        },
        "qubit4": {
            "singleInput": {"port": ("con1", 5)},
            "intermediate_frequency": 5e6,
            "operations": {
                "pi": "pi_single",
            },
        },
        "laser_red_Ey": {
            "digitalInputs": {
                "laser_red": {"buffer": 0, "delay": 0, "port": ("con1", 5)},
            },
            "operations": {
                "laser_pi": "laser_pi",
                "laser_on": "laser_red",
            },
        },
    },
    "pulses": {
        "pi": {
            "operation": "control",
            "length": pi_length,
            "waveforms": {
                "I": "pi_wf",
                "Q": "zero_wf",
            },
        },
        "pi_single": {
            "operation": "control",
            "length": 1000,
            "waveforms": {"single": "const_wf"},
        },
        "pi_2ns": {
            "operation": "control",
            "length": pi_length/2,
            "waveforms": {"I": "pi_wf_2ns", "Q": "zero_wf"},
        },
        "pi_half": {
            "operation": "control",
            "length": pi_length / 2,
            "waveforms": {
                "I": "pi_wf",
                "Q": "zero_wf",
            },
        },
        "laser_on": {
            "digital_marker": "ON",
            "length": init_len,
            "operation": "control",
            "waveforms": {
                "I": "zero_wf",
                "Q": "zero_wf",
            },
        },
        "readout": {
            "digital_marker": "ON",
            "length": readout_len,
            "operation": "measurement",
            "waveforms": {
                "I": "zero_wf",
                "Q": "zero_wf",
            },
        },
        "readout_red": {
            "length": readout_len,
            "operation": "measurement",
            "waveforms": {
                "I": "zero_wf",
                "Q": "zero_wf",
            },
        },
        "entanglement_readout": {
            "digital_marker": "ON",
            "length": ent_len,
            "operation": "measurement",
            "waveforms": {
                "I": "zero_wf",
                "Q": "zero_wf",
            },
        },
        "laser_pi": {
            "digital_marker": "ON_red",
            "length": red_length,
            "operation": "control",
        },
        "laser_red": {
            "digital_marker": "ON",
            "length": readout_len,
            "operation": "control",
        },
    },
    "digital_waveforms":{
            "ON": {"samples": [(1, 0)]
                   },
            "ON_red": {"samples": [(1, 2),(0, 14),(1, 0)]
                       }
        },
    "waveforms": {
        "pi_wf": {"type": "constant", "sample": pi_amplitude},
        "pi_wf_2ns": {
            "type": "arbitrary",
            "samples": [0]*2 + [pi_amplitude] * int(pi_length/2 - 2),
        },
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
}
