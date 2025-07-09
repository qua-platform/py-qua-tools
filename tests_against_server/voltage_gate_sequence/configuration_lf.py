"""
QUA-Config supporting OPX1000 w/ LF-FEM
"""

from pathlib import Path

import numpy as np
from qualang_tools.units import unit
from qualang_tools.voltage_gates import VoltageGateSequence
import plotly.io as pio

pio.renderers.default = "browser"

#######################
# AUXILIARY FUNCTIONS #
#######################
u = unit(coerce_to_integer=True)

######################
# Network parameters #
######################
qop_ip = "127.0.0.1"  # Write the QM router IP address
cluster_name = "my_cluster"  # Write your cluster_name if version >= QOP220
qop_port = None  # Write the QOP port if version < QOP220

#############
# Save Path #
#############
# Path to save data
save_dir = Path(__file__).parent.resolve() / "Data"
save_dir.mkdir(exist_ok=True)

default_additional_files = {
    Path(__file__).name: Path(__file__).name,
    "optimal_weights.npz": "optimal_weights.npz",
}

#####################
# OPX configuration #
#####################
con = "con1"
fem = 5  # Should be the LF-FEM index, e.g., 1
port_P1 = 6  # --> scope 7
port_P2 = 3

# For the automatic testing
MAX_AMP = 0.8
sampling_rate = 2

# Set octave_config to None if no octave are present
octave_config = None

#############################################
#              OPX PARAMETERS               #
#############################################

######################
#       READOUT      #
######################
u = unit(coerce_to_integer=True)

# DC readout parameters
readout_len = 1 * u.us
readout_amp = 0.0
IV_scale_factor = 0.5e-9  # in A/V

# Reflectometry
resonator_IF = 151 * u.MHz
reflectometry_readout_length = 1 * u.us
reflectometry_readout_amp = 30 * u.mV

# Time of flight
time_of_flight = 28

######################
#      DC GATES      #
######################

## Section defining the points from the charge stability map - can be done in the config
# Relevant points in the charge stability map as ["P1", "P2"] in V
level_init = [0.1, -0.1]
level_manip = [0.7, -0.7]
level_readout = [0.12, -0.12]

# Duration of each step in ns
duration_init = 30000
duration_manip = 5000
duration_readout = readout_len + 100
duration_compensation_pulse = 4 * u.us

# Step parameters
step_length = 16  # in ns
P1_step_amp = 0.25  # in V
P2_step_amp = 0.25  # in V
charge_sensor_amp = 0.25  # in V

# Time to ramp down to zero for sticky elements in ns
hold_offset_duration = 4

bias_tee_cut_off_frequency = 10 * u.kHz

######################
#    QUBIT PULSES    #
######################
# Durations in ns
pi_length = 32
pi_half_length = 16
# Amplitudes in V
pi_amps = [0.27, -0.27]
pi_half_amps = [0.27, -0.27]


#############################################
#                  Config                   #
#############################################
config = {
    "version": 1,
    "controllers": {
        con: {
            "type": "opx1000",
            "fems": {
                fem: {
                    "type": "LF",
                    "analog_outputs": {
                        # P1
                        port_P1: {
                            # DC Offset applied to the analog output at the beginning of a program.
                            "offset": 0.0,
                            # The "output_mode" can be used to tailor the max voltage and frequency bandwidth, i.e.,
                            #   "direct":    1Vpp (-0.5V to 0.5V), 750MHz bandwidth (default)
                            #   "amplified": 5Vpp (-2.5V to 2.5V), 330MHz bandwidth
                            # Note, 'offset' takes absolute values, e.g., if in amplified mode and want to output 2.0 V, then set "offset": 2.0
                            "output_mode": "amplified",
                            # The "sampling_rate" can be adjusted by using more FEM cores, i.e.,
                            #   1 GS/s: uses one core per output (default)
                            #   2 GS/s: uses two cores per output
                            # NOTE: duration parameterization of arb. waveforms, sticky elements and chirping
                            #       aren't yet supported in 2 GS/s.
                            "sampling_rate": 1e9,
                            # At 1 GS/s, use the "upsampling_mode" to optimize output for
                            #   modulated pulses (optimized for modulated pulses):      "mw"    (default)
                            #   unmodulated pulses (optimized for clean step response): "pulse"
                            "upsampling_mode": "pulse",
                        },
                        # P2
                        port_P2: {
                            "offset": 0.0,
                            # "output_mode": "amplified",
                            "output_mode": "direct",
                            "sampling_rate": 1e9,
                            "upsampling_mode": "pulse",
                        },
                        # Sensor gate
                        3: {
                            "offset": 0.0,
                            "output_mode": "direct",
                            "sampling_rate": 1e9,
                            "upsampling_mode": "pulse",
                        },
                        # RF Reflectometry
                        7: {
                            "offset": 0.0,
                            "output_mode": "direct",
                            "sampling_rate": 1e9,
                            "upsampling_mode": "mw",
                        },
                        # DC readout
                        8: {
                            "offset": 0.0,
                            "output_mode": "direct",
                            "sampling_rate": 1e9,
                            "upsampling_mode": "pulse",
                        },
                    },
                    "digital_outputs": {
                        1: {},  # TTL for QDAC
                        2: {},  # TTL for QDAC
                    },
                    "analog_inputs": {
                        1: {"offset": 0.0, "gain_db": 0, "sampling_rate": 1e9},  # RF reflectometry input
                        2: {"offset": 0.0, "gain_db": 0, "sampling_rate": 1e9},  # DC readout input
                    },
                }
            },
        }
    },
    "elements": {
        "P1": {
            "singleInput": {
                "port": (con, fem, port_P1),
            },
            "operations": {
                "step": "P1_step_pulse",
                "pi": "P1_pi_pulse",
                "pi_half": "P1_pi_half_pulse",
            },
        },
        "P1_sticky": {
            "singleInput": {
                "port": (con, fem, port_P1),
            },
            "sticky": {"analog": True, "duration": hold_offset_duration},
            "operations": {
                "step": "P1_step_pulse",
            },
        },
        "P2": {
            "singleInput": {
                "port": (con, fem, port_P2),
            },
            "operations": {
                "step": "P2_step_pulse",
                "pi": "P2_pi_pulse",
                "pi_half": "P2_pi_half_pulse",
            },
        },
        "P2_sticky": {
            "singleInput": {
                "port": (con, fem, port_P2),
            },
            "sticky": {"analog": True, "duration": hold_offset_duration},
            "operations": {
                "step": "P2_step_pulse",
            },
        },
        "sensor_gate": {
            "singleInput": {
                "port": (con, fem, 3),
            },
            "operations": {
                "step": "bias_charge_pulse",
            },
        },
        "sensor_gate_sticky": {
            "singleInput": {
                "port": (con, fem, 3),
            },
            "sticky": {"analog": True, "duration": hold_offset_duration},
            "operations": {
                "step": "bias_charge_pulse",
            },
        },
        "qdac_trigger1": {
            "digitalInputs": {
                "trigger": {
                    "port": (con, fem, 1),
                    "delay": 0,
                    "buffer": 0,
                }
            },
            "operations": {
                "trigger": "trigger_pulse",
            },
        },
        "qdac_trigger2": {
            "digitalInputs": {
                "trigger": {
                    "port": (con, fem, 2),
                    "delay": 0,
                    "buffer": 0,
                }
            },
            "operations": {
                "trigger": "trigger_pulse",
            },
        },
        "tank_circuit": {
            "singleInput": {
                "port": (con, fem, 7),
            },
            "intermediate_frequency": resonator_IF,
            "operations": {
                "readout": "reflectometry_readout_pulse",
            },
            "outputs": {
                "out1": (con, fem, 1),
                "out2": (con, fem, 2),
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
        "TIA": {
            "singleInput": {
                "port": (con, fem, 8),
            },
            "operations": {
                "readout": "readout_pulse",
            },
            "outputs": {
                "out1": (con, fem, 1),
                "out2": (con, fem, 2),
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
    },
    "pulses": {
        "P1_pi_pulse": {
            "operation": "control",
            "length": pi_length,
            "waveforms": {
                "single": "P1_pi_wf",
            },
        },
        "P1_pi_half_pulse": {
            "operation": "control",
            "length": pi_half_length,
            "waveforms": {
                "single": "P1_pi_half_wf",
            },
        },
        "P2_pi_pulse": {
            "operation": "control",
            "length": pi_length,
            "waveforms": {
                "single": "P2_pi_wf",
            },
        },
        "P2_pi_half_pulse": {
            "operation": "control",
            "length": pi_half_length,
            "waveforms": {
                "single": "P2_pi_half_wf",
            },
        },
        "P1_step_pulse": {
            "operation": "control",
            "length": step_length,
            "waveforms": {
                "single": "P1_step_wf",
            },
        },
        "P2_step_pulse": {
            "operation": "control",
            "length": step_length,
            "waveforms": {
                "single": "P2_step_wf",
            },
        },
        "bias_charge_pulse": {
            "operation": "control",
            "length": step_length,
            "waveforms": {
                "single": "charge_sensor_step_wf",
            },
        },
        "trigger_pulse": {
            "operation": "control",
            "length": 100,
            "digital_marker": "ON",
        },
        "reflectometry_readout_pulse": {
            "operation": "measurement",
            "length": reflectometry_readout_length,
            "waveforms": {
                "single": "reflect_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
            },
            "digital_marker": "ON",
        },
        "readout_pulse": {
            "operation": "measurement",
            "length": readout_len,
            "waveforms": {
                "single": "readout_pulse_wf",
            },
            "integration_weights": {
                "constant": "constant_weights",
            },
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "P1_pi_wf": {"type": "constant", "sample": pi_amps[0] - level_manip[0]},
        "P1_pi_half_wf": {"type": "constant", "sample": pi_half_amps[0] - level_manip[0]},
        "P2_pi_wf": {"type": "constant", "sample": pi_amps[1] - level_manip[1]},
        "P2_pi_half_wf": {"type": "constant", "sample": pi_half_amps[1] - level_manip[1]},
        "P1_step_wf": {"type": "constant", "sample": P1_step_amp},
        "P2_step_wf": {"type": "constant", "sample": P2_step_amp},
        "charge_sensor_step_wf": {"type": "constant", "sample": charge_sensor_amp},
        "readout_pulse_wf": {"type": "constant", "sample": readout_amp},
        "reflect_wf": {"type": "constant", "sample": reflectometry_readout_amp},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
    "integration_weights": {
        "constant_weights": {
            "cosine": [(1, readout_len)],
            "sine": [(0.0, readout_len)],
        },
        "cosine_weights": {
            "cosine": [(1.0, reflectometry_readout_length)],
            "sine": [(0.0, reflectometry_readout_length)],
        },
        "sine_weights": {
            "cosine": [(0.0, reflectometry_readout_length)],
            "sine": [(1.0, reflectometry_readout_length)],
        },
    },
}
