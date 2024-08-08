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
opx_instrument = OPX(config, name="OPX_demo", host=qop_ip, cluster_name=cluster_name)
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

# if run == "raw_adc":
#     # Execute program
#     opx_instrument.qua_program = prog
#     do1d(
#         VP1,
#         10,
#         20,
#         10,
#         0.1,
#         opx_instrument.resume,
#         opx_instrument.get_measurement_parameter(),
#         enter_actions=[opx_instrument.run_exp],
#         exit_actions=[opx_instrument.halt],
#         show_progress=True,
#         do_plot=True,
#         exp=experiment,
#     )
#
#
# #####################################
# #        0D SWEEP & do2d            #
# #####################################
# # Demonstrate how to perform a single point measurement with the OPX
# # by integrating the readout signals while performing an external 2D sweep
# # with the do2d function.
# def OPX_0d_scan(simulate=False):
#     with program() as prog:
#         I = declare(fixed)
#         Q = declare(fixed)
#         Q_st = declare_stream()
#         I_st = declare_stream()
#         with infinite_loop_():
#             if not simulate:
#                 pause()
#             measure(
#                 "readout",
#                 "readout_element",
#                 None,
#                 integration.full("cos", I, "out1"),
#                 integration.full("cos", Q, "out2"),
#             )
#             save(I, I_st)
#             save(Q, Q_st)
#
#         with stream_processing():
#             I_st.save_all("I")
#             Q_st.save_all("Q")
#     return prog
#
#
# if run == "0d":
#     # Add the custom sequence to the OPX
#     opx_instrument.qua_program = OPX_0d_scan(simulate=True)
#     # Simulate program
#     opx_instrument.sim_time(10_000)
#     opx_instrument.simulate()
#     opx_instrument.plot_simulated_wf()
#     # Execute program
#     opx_instrument.qua_program = OPX_0d_scan(simulate=False)
#     do2d(
#         VP1,
#         -5,
#         5,
#         11,
#         0.1,
#         VP2,
#         10,
#         20,
#         7,
#         0.1,
#         opx_instrument.resume,
#         opx_instrument.get_measurement_parameter(),
#         enter_actions=[opx_instrument.run_exp],
#         exit_actions=[opx_instrument.halt],
#         show_progress=True,
#         do_plot=True,
#         exp=experiment,
#     )
#
# #####################################
# #        1D SWEEP & do0d            #
# #####################################
# # Show how to perform a 1D sweep with averaging on the OPX
# # without scanning any external parameter with the do0d function.
# step = 0.01
# biases = np.arange(0, 0.5, 0.01)
# prefactor = step / gate_1_amp
# n_avg = 10
#
#
# # QUA sequence
# def OPX_1d_scan(simulate=False):
#     with program() as prog:
#         i = declare(int)
#         n = declare(int)
#         I = declare(fixed)
#         Q = declare(fixed)
#         Q_st = declare_stream()
#         I_st = declare_stream()
#         with infinite_loop_():
#             if not simulate:
#                 pause()
#             with for_(n, 0, n < n_avg, n + 1):
#                 with for_(i, 0, i < len(biases), i + 1):
#                     with if_(i == 0):
#                         play("bias" * amp(0), "gate_1")
#                     with else_():
#                         play("bias" * amp(prefactor), "gate_1")
#
#                     wait(200 // 4, "readout_element")
#                     measure(
#                         "readout",
#                         "readout_element",
#                         None,
#                         integration.full("cos", I, "out1"),
#                         integration.full("cos", Q, "out2"),
#                     )
#                     save(I, I_st)
#                     save(Q, Q_st)
#                 ramp_to_zero("gate_1")
#
#         with stream_processing():
#             I_st.buffer(len(biases)).buffer(n_avg).map(FUNCTIONS.average()).save_all(
#                 "I"
#             )
#             Q_st.buffer(len(biases)).buffer(n_avg).map(FUNCTIONS.average()).save_all(
#                 "Q"
#             )
#     return prog
#
#
# if run == "1d":
#     # Axis1 is the most inner loop
#     opx_instrument.set_sweep_parameters("axis1", biases, "V", "Biases")
#     # Update the readout length for this experiment
#     readout_length = 600  # in ns
#     opx_instrument.update_readout_length("readout_element", "readout", readout_length)
#     # Pass the readout length (in ns) to the class to convert the demodulated/integrated data into Volts
#     # and create the setpoint Parameter for raw adc trace acquisition
#     opx_instrument.readout_pulse_length(readout_length)
#     # Add the custom sequence to the OPX
#     opx_instrument.qua_program = OPX_1d_scan(simulate=True)
#     # Simulate program
#     opx_instrument.sim_time(10_000)
#     opx_instrument.simulate()
#     opx_instrument.plot_simulated_wf()
#     # Execute program
#     opx_instrument.qua_program = OPX_1d_scan(simulate=False)
#     # Here we add a scale factor to convert the data from V to pA
#     do0d(
#         opx_instrument.run_exp,
#         opx_instrument.resume,
#         opx_instrument.get_measurement_parameter(
#             scale_factor=[("I", 1235, "pA"), ("Q", 1235, "pA")]
#         ),
#         opx_instrument.halt,
#         do_plot=True,
#         exp=experiment,
#     )
#
# #####################################
# #        2D SWEEP & do0d            #
# #####################################
# # Shows how to perform a 2D sweep with the OPX without
# # scanning any external parameters with the do0d function
# gate_1_step = 0.01
# gate_1_biases = np.arange(-0.2, 0.2, gate_1_step)
# gate_1_prefactor = gate_1_step / gate_1_amp
#
# gate_2_step = 0.01
# gate_2_biases = np.arange(0, 0.25, gate_2_step)
# gate_2_prefactor = gate_2_step / gate_2_amp
#
#
# def OPX_2d_scan(simulate=False):
#     with program() as prog:
#         i = declare(int)
#         j = declare(int)
#         I = declare(fixed)
#         Q = declare(fixed)
#         I_st = declare_stream()
#         Q_st = declare_stream()
#         with infinite_loop_():
#             if not simulate:
#                 pause()
#             with for_(i, 0, i < len(gate_1_biases), i + 1):
#                 with if_(i == 0):
#                     play("bias" * amp(0), "gate_1")
#                 with else_():
#                     play("bias" * amp(gate_1_prefactor), "gate_1")
#
#                 with for_(j, 0, j < len(gate_2_biases), j + 1):
#                     with if_(j == 0):
#                         play("bias" * amp(0), "gate_2")
#                     with else_():
#                         play("bias" * amp(gate_2_prefactor), "gate_2")
#
#                     wait(200 // 4, "readout_element")
#                     measure(
#                         "readout",
#                         "readout_element",
#                         None,
#                         integration.full("cos", I, "out1"),
#                         integration.full("cos", Q, "out2"),
#                     )
#                     save(I, I_st)
#                     save(Q, Q_st)
#
#                 ramp_to_zero("gate_2")
#             ramp_to_zero("gate_1")
#
#         with stream_processing():
#             I_st.buffer(len(gate_2_biases)).buffer(len(gate_1_biases)).save_all("I")
#             Q_st.buffer(len(gate_2_biases)).buffer(len(gate_1_biases)).save_all("Q")
#     return prog
#
#
# if run == "2d":
#     # Axis1 is the most inner loop
#     opx_instrument.set_sweep_parameters("axis1", gate_2_biases, "V", "Gate 2 biases")
#     # Axis2 is the second loop
#     opx_instrument.set_sweep_parameters("axis2", gate_1_biases, "V", "Gate 1 biases")
#     # Add the custom sequence to the OPX
#     opx_instrument.qua_program = OPX_2d_scan(simulate=True)
#     # Simulate program
#     opx_instrument.sim_time(100_000)
#     opx_instrument.simulate()
#     opx_instrument.plot_simulated_wf()
#     # Execute program
#     opx_instrument.qua_program = OPX_2d_scan(simulate=False)
#     do0d(
#         opx_instrument.run_exp,
#         opx_instrument.resume,
#         opx_instrument.get_measurement_parameter(),
#         opx_instrument.halt,
#         do_plot=True,
#         exp=experiment,
#     )
#
# #####################################
# #        SLICED INT & do0d          #
# #####################################
# # Shows how to perform a 1D sweep with the OPX and acquire the readout
# # signals using the sliced integration feature to reduce the sampling rate
# # without scanning any external parameter using the do0d function
# slice_size = 4  # Size of one slice in ns (must a multiple of 4)
# nb_of_slices = readout_len // slice_size
# n_avg = 10
# step = 0.01
# biases = np.arange(0, 0.5, 0.01)
# prefactor = step / gate_1_amp
#
#
# def OPX_sliced_scan(simulate=False):
#     with program() as prog:
#         i = declare(int)
#         j = declare(int)
#         n = declare(int)
#         I = declare(fixed, size=nb_of_slices)
#         Q = declare(fixed, size=nb_of_slices)
#         Q_st = declare_stream()
#         I_st = declare_stream()
#         with infinite_loop_():
#             if not simulate:
#                 pause()
#             with for_(n, 0, n < n_avg, n + 1):
#                 with for_(i, 0, i < len(biases), i + 1):
#                     with if_(i == 0):
#                         play("bias" * amp(0), "gate_1")
#                     with else_():
#                         play("bias" * amp(prefactor), "gate_1")
#
#                     wait(200 // 4, "readout_element")
#                     measure(
#                         "readout",
#                         "readout_element",
#                         None,
#                         integration.sliced("cos", I, slice_size // 4, "out1"),
#                         integration.sliced("cos", Q, slice_size // 4, "out2"),
#                     )
#                     with for_(j, 0, j < nb_of_slices, j + 1):
#                         save(I[j], I_st)
#                         save(Q[j], Q_st)
#                 ramp_to_zero("gate_1")
#
#         with stream_processing():
#             I_st.buffer(nb_of_slices).buffer(len(biases)).buffer(n_avg).map(
#                 FUNCTIONS.average()
#             ).save_all("I")
#             Q_st.buffer(nb_of_slices).buffer(len(biases)).buffer(n_avg).map(
#                 FUNCTIONS.average()
#             ).save_all("Q")
#     return prog
#
#
# if run == "sliced":
#     # Axis1 is the most inner loop
#     opx_instrument.set_sweep_parameters(
#         "axis1",
#         np.arange(slice_size / 2, (nb_of_slices + 0.5) * slice_size, slice_size),
#         "ns",
#         "sliced demod",
#     )
#     # Axis2 is the second loop
#     opx_instrument.set_sweep_parameters("axis2", biases, "V", "Biases")
#     # Add the custom sequence to the OPX
#     opx_instrument.qua_program = OPX_sliced_scan(simulate=True)
#     # Simulate program
#     opx_instrument.sim_time(10_000)
#     opx_instrument.simulate()
#     opx_instrument.plot_simulated_wf()
#     # Execute program
#     opx_instrument.qua_program = OPX_sliced_scan(simulate=False)
#     do0d(
#         opx_instrument.run_exp,
#         opx_instrument.resume,
#         opx_instrument.get_measurement_parameter(),
#         opx_instrument.halt,
#         do_plot=True,
#         exp=experiment,
#     )
#
# #####################################
# #     1D OPX SWEEP & datasaver      #
# #####################################
# # Show how to perform a 1D sweep with averaging on the OPX
# # while scanning an external parameter using the qcodes Measurement framework instead of do1d.
# from qualang_tools.loops import from_array
# from qcodes.dataset import plot_dataset
#
# frequencies = np.arange(50e6, 300e6, 0.1e6)
# n_avg = 10
#
#
# # QUA sequence
# def OPX_reflectometry(simulate=False):
#     with program() as prog:
#         f = declare(int)
#         n = declare(int)
#         I = declare(fixed)
#         Q = declare(fixed)
#         Q_st = declare_stream()
#         I_st = declare_stream()
#         with infinite_loop_():
#             if not simulate:
#                 pause()
#             with for_(n, 0, n < n_avg, n + 1):
#                 with for_(*from_array(f, frequencies)):
#                     update_frequency("readout_element", f)
#                     measure(
#                         "readout",
#                         "readout_element",
#                         None,
#                         demod.full("cos", I, "out1"),
#                         demod.full("sin", Q, "out1"),
#                     )
#                     wait(1000, "readout_element")
#                     save(I, I_st)
#                     save(Q, Q_st)
#
#         with stream_processing():
#             I_st.buffer(len(frequencies)).buffer(n_avg).map(
#                 FUNCTIONS.average()
#             ).save_all("I")
#             Q_st.buffer(len(frequencies)).buffer(n_avg).map(
#                 FUNCTIONS.average()
#             ).save_all("Q")
#     return prog
#
#
# if run == "datasaver":
#     # Axis1 is the most inner loop
#     opx_instrument.set_sweep_parameters("axis1", frequencies, "Hz", "Readout frequency")
#     # Add the custom sequence to the OPX
#     opx_instrument.qua_program = OPX_reflectometry(simulate=True)
#     # Simulate program
#     opx_instrument.sim_time(10_000)
#     opx_instrument.simulate()
#     opx_instrument.plot_simulated_wf()
#     # Execute program
#     opx_instrument.qua_program = OPX_reflectometry(simulate=False)
#     # Initialize the measurement
#     meas = qc.Measurement(exp=experiment, name="reflectometry")
#     # Register the qcodes parameter that we'll sweep
#     meas.register_parameter(VP1)
#     # Get the Result parameters from the OPX scan
#     OPX_param = opx_instrument.get_measurement_parameter()
#     # Register all the involved parameters
#     meas.register_parameter(OPX_param, setpoints=[VP1])
#     # Start the sequence (Send the QUA program to the OPX which compiles and executes it)
#     opx_instrument.run_exp()
#     # Start the qcodes measurement
#     with meas.run() as datasaver:
#         # Loop over an external parameter
#         for gate_v in np.arange(0, 0.01, 0.001):
#             # Update ethe external parameter
#             VP1(gate_v)
#             # Run the QUA sequence
#             opx_instrument.resume()
#             # Get the results from the OPX
#             data = opx_instrument.get_res()
#             # Store the results in the scodes database
#             datasaver.add_result(
#                 (VP1, VP1()), (OPX_param, np.array(list(data.values())))
#             )
#         # Halt the OPX program at the end
#         opx_instrument.halt()
#         # Get the full dataset
#         dataset = datasaver.dataset
#     # Plot the dataset
#     plot_dataset(dataset)
