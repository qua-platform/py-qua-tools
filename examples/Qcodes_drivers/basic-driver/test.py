import os
import numpy as np
import qcodes as qc
from qcodes import initialise_or_create_database_at, load_or_create_experiment
from qcodes.utils.dataset.doNd import do2d, do1d, do0d
from qcodes import Parameter
from qm.qua import *
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX
from configuration import *

# %%
import numpy as np
from qualang_tools.config.waveform_tools import drag_gaussian_pulse_waveforms
from qualang_tools.units import unit
from qualang_tools.results.data_handler import DataHandler

#######################
# AUXILIARY FUNCTIONS #
#######################
u = unit(coerce_to_integer=True)

def save_data(data, name):
    _data_handler = DataHandler(root_data_folder="data/")
    _data_handler.save_data(data=data, name=name)

######################
# Network parameters #
######################
qop_ip = "172.16.33.107"  # Akiva OPX1000
cluster_name = "Beta_8"   # Write your cluster_name if version >= QOP220
qop_port = None  # Write the QOP port if version < QOP220
fem = 3
# # Path to save data
# save_dir = Path().absolute() / "data"

#####################
# OPX configuration #
#####################

digital_pulse_len = 100
# Continuous wave
const_len = 100  # ns
const_amp = 0.2  # V
# Square wave
square_up_len = 500
square_down_len = 500
square_amp = 0.5
# Arbitrary pulse
arb_len = 40
arb_amp = 0.2
arb_wf = drag_gaussian_pulse_waveforms(arb_amp, arb_len, arb_len//5, 0.0, 50e6, 0)[0]

##########################################
#                Readout                 #
##########################################
intermediate_frequency = 100 * u.MHz

readout_len = 1 * u.us
readout_amp = 0.3

time_of_flight = 24 + 0*120
depletion_time = 2 * u.us

# IQ Plane Angle
rotation_angle = (0 / 180) * np.pi

# MARK: CONFIGURATION
#############################################
#                  Config                   #
#############################################
def get_config(sampling_rate = 1e9):
    config = {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1000",
                "fems": {
                    fem: {
                        "type": "LF",
                        "analog_outputs": {
                            1: {"offset": 0.0, "sampling_rate": 1e9, "output_mode": "amplified", "upsampling_mode": "pulse", "delay": 0},  # , "filter": {"feedforward": [], "feedback": []}
                            2: {"offset": 0.0, "sampling_rate": 1e9, "output_mode": "amplified", "upsampling_mode": "pulse", "delay": 0},  # , "filter": {"feedforward": [], "feedback": []}
                            3: {"offset": 0.0, "sampling_rate": 1e9, "output_mode": "direct", "upsampling_mode": "pulse", "delay": 0},
                            8: {"offset": 0.0, "sampling_rate": 2e9, "output_mode": "direct", "delay": 0},
                        },
                        "analog_inputs": {
                            1: {"offset": 0.0, "sampling_rate": int(2e9), "gain_db": 0, "shareable": True},
                            2: {"offset": 0.0, "sampling_rate": int(2e9), "gain_db": 0, "shareable": True},
                        },
                        "digital_outputs": {
                        },
                    },
                },
            },
        },
        "elements": {
            "lf_element_1": {
                "singleInput": {
                    "port": ("con1", fem, 1),
                },
                "intermediate_frequency": 0,
                "operations": {
                    "const": "const_single_pulse",
                    "arbitrary": "arbitrary_pulse",
                    "up": "up_pulse",
                    "down": "down_pulse",
                },
            },
            "lf_element_2": {
                "singleInput": {
                    "port": ("con1", fem, 2),
                },
                "intermediate_frequency": 0,
                "operations": {
                    "const": "const_single_pulse",
                    "arbitrary": "arbitrary_pulse",
                    "up": "up_pulse",
                    "down": "down_pulse",
                },
            },
            "scope_trigger": {
                "singleInput": {
                    "port": ("con1", fem, 3),
                },
                "operations": {
                    "const": "const_single_pulse",
                },
            },
            "lf_readout_element": {
                "singleInput": {
                    "port": ("con1", fem, 8),
                },
                "intermediate_frequency": intermediate_frequency,
                "operations": {
                    "readout": "readout_pulse",
                },
                "outputs": {
                    "out1": ("con1", fem, 1),
                },
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
            "lf_readout_element_twin": {
                "singleInput": {
                    "port": ("con1", fem, 8),
                },
                "intermediate_frequency": intermediate_frequency,
                "operations": {
                    "readout": "readout_pulse",
                },
                "outputs": {
                    "out1": ("con1", fem, 1),
                },
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
            "dc_readout_element": {
                "singleInput": {
                    "port": ("con1", fem, 8),
                },
                "operations": {
                    "readout": "dc_readout_pulse",
                },
                "outputs": {
                    "out2": ("con1", fem, 2),
                },
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },
            "dc_readout_element_twin": {
                "singleInput": {
                    "port": ("con1", fem, 8),
                },
                "operations": {
                    "readout": "dc_readout_pulse",
                },
                "outputs": {
                    "out2": ("con1", fem, 2),
                },
                "time_of_flight": time_of_flight,
                "smearing": 0,
            },

        },
        "pulses": {
            "arbitrary_pulse": {
                "operation": "control",
                "length": int(arb_len * 1e9 / 1e9),
                "waveforms": {
                    "single": "arbitrary_wf",
                },
            },
            "bias_pulse": {
                "operation": "control",
                "length": 16,
                "waveforms": {
                    "single": "bias_wf",
                },
            },
            "up_pulse": {
                "operation": "control",
                "length": square_up_len,
                "waveforms": {
                    "single": "up_wf",
                },
            },
            "down_pulse": {
                "operation": "control",
                "length": square_down_len,
                "waveforms": {
                    "single": "down_wf",
                },
            },
            "const_single_pulse": {
                "operation": "control",
                "length": const_len,
                "waveforms": {
                    "single": "const_wf",
                },
            },
            "trigger_pulse": {
                "operation": "control",
                "length": 10000,
                "digital_marker": "ON",
            },
            "const_pulse_mw": {
                "operation": "control",
                "length": const_len,
                "waveforms": {
                    "I": "const_wf",
                    "Q": "zero_wf",
                },
            },
            "switchON_pulse": {
                "operation": "control",
                "length": digital_pulse_len,
                "digital_marker": "ON",
            },
            "switchOFF_pulse": {
                "operation": "control",
                "length": digital_pulse_len,
                "digital_marker": "OFF",
            },
            "readout_pulse": {
                "operation": "measurement",
                "length": readout_len,
                "waveforms": {
                    "single": "readout_wf",
                },
                "integration_weights": {
                    "cos": "cosine_weights",
                    "sin": "sine_weights",
                    "minus_sin": "minus_sine_weights",
                    "rotated_cos": "rotated_cosine_weights",
                    "rotated_sin": "rotated_sine_weights",
                    "rotated_minus_sin": "rotated_minus_sine_weights",
                },
                "digital_marker": "ON",
            },
            "dc_readout_pulse": {
                "operation": "measurement",
                "length": readout_len,
                "waveforms": {
                    "single": "dc_readout_wf",
                },
                "integration_weights": {
                    "const": "const_weights",
                },
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": const_amp},
            "bias_wf": {"type": "constant", "sample": 0.25},
            "up_wf": {"type": "constant", "sample": square_amp},
            "down_wf": {"type": "constant", "sample": -square_amp},
            "readout_wf": {"type": "constant", "sample": readout_amp},
            "dc_readout_wf": {"type": "constant", "sample": readout_amp},
            "arbitrary_wf": {"type": "arbitrary", "samples": arb_wf, "sampling_rate": 1e9},

        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
            "OFF": {"samples": [(0, 0)]},
        },
        "integration_weights": {
            "const_weights": {
                "cosine": [(1.0, readout_len)],
                "sine": [(0.0, readout_len)],
            },
            "cosine_weights": {
                "cosine": [(0.1, readout_len)],
                "sine": [(0.0, readout_len)],
            },
            "sine_weights": {
                "cosine": [(0.0, readout_len)],
                "sine": [(0.1, readout_len)],
            },
            "minus_sine_weights": {
                "cosine": [(0.0, readout_len)],
                "sine": [(-0.1, readout_len)],
            },
            "rotated_cosine_weights": {
                "cosine": [(np.cos(rotation_angle), readout_len)],
                "sine": [(np.sin(rotation_angle), readout_len)],
            },
            "rotated_sine_weights": {
                "cosine": [(-np.sin(rotation_angle), readout_len)],
                "sine": [(np.cos(rotation_angle), readout_len)],
            },
            "rotated_minus_sine_weights": {
                "cosine": [(np.sin(rotation_angle), readout_len)],
                "sine": [(-np.cos(rotation_angle), readout_len)],
            },
        },
    }
    # if sampling_rate == 1e9:
    #     config["elements"]["lf_element_1_sticky"] = {
    #         "singleInput": {
    #             "port": ("con1", fem, 1),
    #         },
    #         "intermediate_frequency": 0,
    #         "operations": {
    #             "const": "const_single_pulse",
    #             "bias": "bias_pulse",
    #             "arbitrary": "arbitrary_pulse",
    #             "up": "up_pulse",
    #             "down": "down_pulse",
    #         },
    #         'sticky': {
    #             'analog': True,
    #             'duration': 200
    #         },
    #     }
    #     config["elements"]["lf_element_2_sticky"] = {
    #         "singleInput": {
    #             "port": ("con1", fem, 2),
    #         },
    #         "intermediate_frequency": 0,
    #         "operations": {
    #             "const": "const_single_pulse",
    #             "bias": "bias_pulse",
    #             "arbitrary": "arbitrary_pulse",
    #             "up": "up_pulse",
    #             "down": "down_pulse",
    #         },
    #         'sticky': {
    #             'analog': True,
    #             'duration': 200
    #         },
    #     }
    return config

# config = get_config(1e9)
#####################################
#           Qcodes set-up           #
#####################################
db_name = "QM_demo.db"  # Database name
sample_name = "demo"  # Sample name
exp_name = "OPX_qcodes_drivers"  # Experiment name

# Initialize qcodes database
db_file_path = os.path.join(os.getcwd(), db_name)
qc.config.core.db_location = db_file_path
initialise_or_create_database_at(db_file_path)
# Initialize qcodes experiment
experiment = load_or_create_experiment(
    experiment_name=exp_name, sample_name=sample_name
)
# Initialize the qcodes station to which instruments will be added
station = qc.Station()
# Create the OPX instrument class
opx_instrument = OPX(get_config(), name="OPX_demo", host=qop_ip, cluster_name=cluster_name)
# Add the OPX instrument to the qcodes station
station.add_component(opx_instrument)


# Create fake parameters for do1d and do2d scan demonstration, can be replaced by external instrument parameters
class MyCounter(Parameter):
    def __init__(self, name, label):
        # only name is required
        super().__init__(
            name=name,
            label=label,
            unit="V",
            docstring="Dummy counter for scanning a variable with qcodes",
        )
        self._count = 0

    # you must provide a get method, a set method, or both.
    def get_raw(self):
        self._count += 1
        return self._count

    def set_raw(self, val):
        self._count = val
        return self._count


VP1 = MyCounter("counter1", "Vp1")
VP2 = MyCounter("counter2", "Vp2")

#####################################
run = "1d"
# Pass the readout length (in ns) to the class to convert the demodulated/integrated data into Volts
# and create the setpoint Parameter for raw adc trace acquisition
opx_instrument.readout_pulse_length(readout_len)
#####################################
#     Raw ADC trace & do1d          #
#####################################
# Demonstrate how to acquire the raw adc traces of
# the OPX while sweep an external parameter with the
# do1d function.

with program() as prog:
    adc_st = declare_stream(adc_trace=True)
    with infinite_loop_():
        pause()
        play("bias", "gate_1")
        wait(200 // 4, "readout_element")
        measure("readout", "readout_element", adc_st)
        align()
        ramp_to_zero("gate_1")

    with stream_processing():
        adc_st.input1().save_all("adc1")
        adc_st.input2().save_all("adc2")
