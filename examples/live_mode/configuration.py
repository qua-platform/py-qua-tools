from qualang_tools.units import unit


######################
# AUXILIARY FUNCTIONS:
######################
u = unit()

######################
# Network parameters #
######################
qop_ip = "127.0.0.1"  # Write the QM router IP address
cluster_name = "my_cluster"  # Write your cluster_name if version >= QOP220
qop_port = None  # Write the QOP port if version < QOP220


################
# CONFIGURATION:
################
# Phase modulation
phase_modulation_IF = 5 * u.MHz
phase_mod_amplitude = 0.1
phase_mod_len = 10 * u.us

# AOM
AOM_IF = 0
const_amplitude = 0.1
const_len = 100

# Filter cavity
offset_amplitude = 0.25  # Fixed do not change
offset_len = 16  # Fixed do not change

# Photo-diode
readout_len = phase_mod_len
time_of_flight = 192


config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                8: {"offset": 0.0},
                9: {"offset": 0.0},
                10: {"offset": 0.0},
            },
            "digital_outputs": {
                1: {},
            },
            "analog_inputs": {
                1: {"offset": 0.0},
                2: {"offset": 0.0},
            },
        }
    },
    "elements": {
        "phase_modulator": {
            "singleInput": {
                "port": ("con1", 8),
            },
            "intermediate_frequency": phase_modulation_IF,
            "operations": {
                "cw": "phase_mod_pulse",
            },
        },
        "filter_cavity_1": {
            "singleInput": {
                "port": ("con1", 9),
            },
            "operations": {
                "offset": "offset_pulse",
            },
            "sticky": {"analog": True, "duration": 60},
        },
        "filter_cavity_2": {
            "singleInput": {
                "port": ("con1", 10),
            },
            "operations": {
                "offset": "offset_pulse",
            },
            "sticky": {"analog": True, "duration": 60},
        },
        "detector_DC": {
            "singleInput": {
                "port": ("con1", 9),
            },
            "operations": {
                "readout": "DC_readout_pulse",
            },
            "outputs": {
                "out1": ("con1", 1),
                "out2": ("con1", 2),
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
        "detector_AC": {
            "singleInput": {
                "port": ("con1", 9),
            },
            "intermediate_frequency": phase_modulation_IF,
            "operations": {
                "readout": "AC_readout_pulse",
            },
            "outputs": {
                "out1": ("con1", 1),
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
    },
    "pulses": {
        "offset_pulse": {
            "operation": "control",
            "length": offset_len,
            "waveforms": {
                "single": "offset_wf",
            },
        },
        "phase_mod_pulse": {
            "operation": "control",
            "length": phase_mod_len,
            "waveforms": {
                "single": "phase_mod_wf",
            },
        },
        "cw_pulse": {
            "operation": "control",
            "length": const_len,
            "waveforms": {
                "single": "const_wf",
            },
        },
        "DC_readout_pulse": {
            "operation": "measurement",
            "length": readout_len,
            "waveforms": {
                "single": "zero_wf",
            },
            "integration_weights": {
                "constant": "constant_weights",
            },
            "digital_marker": "ON",
        },
        "AC_readout_pulse": {
            "operation": "measurement",
            "length": readout_len,
            "waveforms": {
                "single": "zero_wf",
            },
            "integration_weights": {
                "constant": "constant_weights",
            },
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "phase_mod_wf": {"type": "constant", "sample": phase_mod_amplitude},
        "const_wf": {"type": "constant", "sample": const_amplitude},
        "offset_wf": {"type": "constant", "sample": offset_amplitude},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
    "integration_weights": {
        "constant_weights": {
            "cosine": [(1.0, readout_len)],
            "sine": [(0.0, readout_len)],
        },
    },
}
