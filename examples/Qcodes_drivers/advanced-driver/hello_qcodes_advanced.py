import os
import qcodes as qc
from qcodes import initialise_or_create_database_at, load_or_create_experiment
from qcodes.utils.dataset.doNd import do2d, do1d, do0d
from qcodes import Parameter
from qm.qua import *
from qualang_tools.loops import from_array
from advanced_driver import OPXCustomSequence
from configuration import *


#####################################
#           Qcodes set-up           #
#####################################
db_name = "QM_demo.db"  # Database name
sample_name = "demo"  # Sample name
exp_name = "OPX_advanced_driver"  # Experiment name

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
opx_instrument = OPXCustomSequence(config, name="OPX_demo", host="127.0.0.1")
# Add the OPX instrument to the qcodes station
station.add_component(opx_instrument)
# Create fake parameters for do1d and do2d scan demonstration, can be replaced by external instrument parameters
class MyCounter(Parameter):
    def __init__(self, label):
        # only name is required
        super().__init__(
            name="my_counter",
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


VP1 = MyCounter("Vp1")
VP2 = MyCounter("Vp2")

#####################################
#        OPX sequence set-up        #
#####################################
# Specific mode for which the OPX executes its pulse sequence when a trigger is received.
opx_instrument.wait_for_trigger(False)
# Parametrize the OPX readout scheme. The config will be updated locally.
opx_instrument.readout_element("resonator")  # Set the readout element
opx_instrument.readout_operation("readout")  # Set the readout operation
opx_instrument.readout_pulse_length(1_000)  # Set the readout duration in ns
opx_instrument.readout_pulse_amplitude(0.01)  # Set the readout amplitude in V
# OPX simulation mode
opx_instrument.simulation(True)
opx_instrument.sim_time(11_000)  # Simulation duration in ns
run = "rabi_2d"
#######################################
#     Power Rabi vs external flux     #
#######################################
if run == "rabi_1d":
    n_avg = 100
    amp_vec = np.arange(0, 1.9, 0.02)
    # QUA sequence
    def custom_sequence(self):
        n = declare(int)
        a = declare(fixed)
        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(a, amp_vec)):
                play("cw" * amp(a), "qubit")
                align()
                self.measurement()
                align()
                wait(100, "qubit")

    # Parametrize the OPX sweep
    # Dimension of the sweeps performed by the OPX. Can be '0d', '1d' or '2d'
    opx_instrument.opx_scan("1d")
    # Position of the averaging loop in a 2d OPX scan. False means that the averaging loop happens between axis1 and axis2.
    opx_instrument.outer_averaging_loop(True)
    opx_instrument.n_avg(n_avg)
    # Axis1 is the most inner loop
    opx_instrument.set_sweep_parameters(
        "axis1",
        amp_vec * config["waveforms"]["const_wf"]["sample"],
        "V",
        "pulse amplitude",
    )
    # Add the custom sequence to the OPX
    opx_instrument.pulse_sequence = custom_sequence
    # Set the acquisition mode of the OPX among:
    # 'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'
    opx_instrument.acquisition_mode("full_demodulation")
    # Qcodes acquisition mode
    qcodes_do_nd = "do1d"

###################################################
#     Rabi Chevron with middle averaging loop     #
###################################################
if run == "rabi_2d":
    n_avg = 100
    amp_vec = np.arange(0.1, 1.9, 0.02)
    pulse_lengths = np.arange(4, 1000, 10)
    # QUA sequence
    def custom_sequence(self):
        n = declare(int)
        t = declare(int)
        a = declare(fixed)
        with for_(*from_array(a, amp_vec)):
            with for_(n, 0, n < n_avg, n + 1):
                with for_(*from_array(t, pulse_lengths)):
                    play("cw" * amp(a), "qubit", duration=t)
                    align()
                    self.measurement()
                    align()
                    wait(100, "qubit")

    # Parametrize the OPX sweep
    # Dimension of the sweeps performed by the OPX. Can be '0d', '1d' or '2d'
    opx_instrument.opx_scan("2d")
    # Position of the averaging loop in a 2d OPX scan. False means that the averaging loop happens between axis1 and axis2.
    opx_instrument.outer_averaging_loop(False)
    opx_instrument.n_avg(n_avg)
    # Axis1 is the most inner loop
    opx_instrument.set_sweep_parameters(
        "axis1", pulse_lengths * 4, "ns", "pulse duration"
    )
    # Axis2 is the second loop
    opx_instrument.set_sweep_parameters(
        "axis2",
        amp_vec * config["waveforms"]["const_wf"]["sample"],
        "V",
        "pulse amplitude",
    )
    # Add the custom sequence to the OPX
    opx_instrument.pulse_sequence = custom_sequence
    # Set the acquisition mode of the OPX among:
    # 'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'
    opx_instrument.acquisition_mode("full_demodulation")
    # Qcodes acquisition mode
    qcodes_do_nd = "do0d"

#######################################
#    Sliced integration with do1d     #
#######################################
if run == "sliced":
    n_avg = 100
    slice_size = 20  # Size of one slice in ns (must a multiple of 4)
    nb_of_slices = opx_instrument.readout_pulse_length() // slice_size
    # QUA sequence
    def custom_sequence(self):
        n = declare(int)
        with for_(n, 0, n < n_avg, n + 1):
            self.measurement()

    # Parametrize the OPX sweep
    # Dimension of the sweeps performed by the OPX. Can be '0d', '1d' or '2d'
    opx_instrument.opx_scan("0d")
    # Position of the averaging loop in a 2d OPX scan. False means that the averaging loop happens between axis1 and axis2.
    opx_instrument.outer_averaging_loop(True)
    opx_instrument.n_avg(n_avg)
    # Slice length in clock cycles for sliced demodulation/integration
    opx_instrument.slice_size(slice_size // 4)
    # Axis1 for the setpoint corresponding to sliced demod or int
    opx_instrument.set_sweep_parameters(
        "axis1",
        np.arange(slice_size / 2, (nb_of_slices + 0.5) * slice_size, slice_size),
        "ns",
        "pulse duration",
    )
    # Add the custom sequence to the OPX
    opx_instrument.pulse_sequence = custom_sequence
    # Set the acquisition mode of the OPX among:
    # 'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'
    opx_instrument.acquisition_mode("sliced_integration")
    # Qcodes acquisition mode
    qcodes_do_nd = "do1d"

#####################################
#        Run OPX experiment         #
#####################################
if opx_instrument.simulation():
    opx_instrument.sim_time(100_000)
    opx_instrument.simulate()
    opx_instrument.plot_simulated_wf()
elif qcodes_do_nd == "do0d":
    do0d(
        opx_instrument.run_exp,
        opx_instrument.resume,
        opx_instrument.get_measurement_parameter(),
        opx_instrument.halt,
        do_plot=True,
        exp=experiment,
    )
elif qcodes_do_nd == "do1d":
    do1d(
        VP1,
        -10,
        10,
        10,
        0.1,
        opx_instrument.resume,
        opx_instrument.get_measurement_parameter(),
        enter_actions=[opx_instrument.run_exp],
        exit_actions=[opx_instrument.halt],
        show_progress=True,
        do_plot=True,
        exp=experiment,
    )
elif qcodes_do_nd == "do2d":
    do2d(
        VP1,
        10,
        20,
        10,
        0.1,
        VP2,
        10,
        20,
        7,
        0.1,
        opx_instrument.resume,
        opx_instrument.get_measurement_parameter(),
        enter_actions=[opx_instrument.run_exp],
        exit_actions=[opx_instrument.halt],
        show_progress=True,
        do_plot=True,
        exp=experiment,
    )
