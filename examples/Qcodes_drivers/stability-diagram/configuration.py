#############
# VARIABLES #
#############
qop_ip = "127.0.0.1"

readout_len = 100
readout_amp = 0.001

time_of_flight = 300
hold_offset_duration = 200

gate_1_amp = 0.25
gate_2_amp = 0.25

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                1: {"offset": 0.0},
                2: {"offset": 0.0},
                3: {"offset": 0.0},
            },
            "analog_inputs": {
                1: {"offset": 0.0, "gain_db": 0},
                2: {"offset": 0.0, "gain_db": 0},
            },
        },
    },
    "elements": {
        "gate_1": {
            "singleInput": {
                "port": ("con1", 1),
            },
            "hold_offset": {"duration": hold_offset_duration},  # in clock cycles (4ns)
            "operations": {
                "bias": "bias_gate_1_pulse",
            },
        },
        "gate_2": {
            "singleInput": {
                "port": ("con1", 2),
            },
            "hold_offset": {"duration": hold_offset_duration},  # in clock cycles (4ns)
            "operations": {
                "bias": "bias_gate_2_pulse",
            },
        },
        "readout_element": {
            "singleInput": {
                "port": ("con1", 3),
            },
            "operations": {
                "readout": "readout_pulse",
            },
            "outputs": {
                "out1": ("con1", 1),
                "out2": ("con1", 2),
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
    },
    "pulses": {
        "bias_gate_1_pulse": {
            "operation": "control",
            "length": 16,
            "waveforms": {
                "single": "bias_gate_1_pulse_wf",
            },
        },
        "bias_gate_2_pulse": {
            "operation": "control",
            "length": 16,
            "waveforms": {
                "single": "bias_gate_2_pulse_wf",
            },
        },
        "readout_pulse": {
            "operation": "measurement",
            "length": readout_len,
            "waveforms": {
                "single": "readout_pulse_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
                "minus_sin": "minus_sine_weights",
            },
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "bias_gate_1_pulse_wf": {"type": "constant", "sample": gate_1_amp},
        "bias_gate_2_pulse_wf": {"type": "constant", "sample": gate_2_amp},
        "readout_pulse_wf": {"type": "constant", "sample": readout_amp},
        "zero_wf": {"type": "constant", "sample": 0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
    "integration_weights": {
        "cosine_weights": {
            "cosine": [(1.0, readout_len)],
            "sine": [(0.0, readout_len)],
        },
        "sine_weights": {
            "cosine": [(0.0, readout_len)],
            "sine": [(1.0, readout_len)],
        },
        "minus_sine_weights": {
            "cosine": [(0.0, readout_len)],
            "sine": [(-1.0, readout_len)],
        },
    },
}
