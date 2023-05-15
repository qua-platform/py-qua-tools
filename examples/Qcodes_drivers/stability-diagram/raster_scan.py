import os
import qcodes as qc
from qcodes import initialise_or_create_database_at, load_or_create_experiment
from qcodes.utils.dataset.doNd import do2d, do1d, do0d
from qcodes import Parameter
from qm.qua import *
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX
from configuration import *


#####################################
#           Qcodes set-up           #
#####################################
db_name = "QM_demo.db"  # Database name
sample_name = "raster"  # Sample name
exp_name = "Stability diagram"  # Experiment name

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
opx_instrument = OPX(config, name="OPX", host="172.16.33.100", port=81)
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
# Pass the readout length (in ns) to the class to convert the demodulated/integrated data into Volts
# and create the setpoint Parameter for raw adc trace acquisition
opx_instrument.readout_pulse_length(readout_len)

#################################
#        raster scan            #
#################################

V1_min = -0.02
V1_max = 0.02
N1 = 15
V1_setpoints = np.linspace(V1_min, V1_max, N1)
V2_min = 0.233
V2_max = 0.248
N2 = 12
V2_setpoints = np.linspace(V2_min, V2_max, N2)
wait_time = 100
n_avg = 1000

# qm.set_output_dc_offset_by_element("gate_2", "single", V2_min)
# qm.set_output_dc_offset_by_element("gate_1", "single", V1_min)
pulse = config["elements"]["gate_1"]["operations"]["bias"]
wf = config["pulses"][pulse]["waveforms"]["single"]
dy = (V2_max - V2_min) / ((N2 - 1) * config["waveforms"][wf].get("sample"))
dx = (V1_max - V1_min) / ((N1 - 1) * config["waveforms"][wf].get("sample"))


def raster_scan(simulate=False):
    with program() as prog:
        n = declare(int)
        x = declare(int)
        y = declare(int)
        I = declare(fixed)
        Q = declare(fixed)
        V1 = declare(fixed, value=V1_min)
        V2 = declare(fixed, value=V2_min)
        V1_st = declare_stream()
        V2_st = declare_stream()
        I_st = declare_stream()
        Q_st = declare_stream()
        with infinite_loop_():
            if not simulate:
                pause()
            with for_(n, 0, n < n_avg, n + 1):
                ramp_to_zero("gate_1", duration=4)
                ramp_to_zero("gate_2", duration=4)
                assign(V1, V1_min)
                assign(V2, V2_min)
                with for_(y, 0, y < N2, y + 1):
                    with if_(y > 0):
                        play("bias" * amp(dy), "gate_2")
                        assign(V2, V2 + dy * config["waveforms"][wf].get("sample"))
                    ramp_to_zero("gate_1", duration=4)
                    assign(V1, V1_min)
                    with for_(x, 0, x < N1, x + 1):
                        with if_(x > 0):
                            play("bias" * amp(dx), "gate_1")
                            assign(V1, V1 + dx * config["waveforms"][wf].get("sample"))
                        align()
                        wait(wait_time, "readout_element")
                        measure(
                            "readout",
                            "readout_element",
                            None,
                            integration.full("cos", I, "out1"),
                            integration.full("cos", Q, "out2"),
                        )
                        save(V1, V1_st)
                        save(V2, V2_st)
                        save(I, I_st)
                        save(Q, Q_st)
        with stream_processing():
            I_st.buffer(N1).buffer(N2).buffer(n_avg).map(FUNCTIONS.average()).save_all(
                "I"
            )
            Q_st.buffer(N1).buffer(N2).buffer(n_avg).map(FUNCTIONS.average()).save_all(
                "Q"
            )

    return prog


# Axis1 is the most inner loop
opx_instrument.set_sweep_parameters("axis1", V1_setpoints, "V", "Gate 1 biases")
# Axis2 is the second loop
opx_instrument.set_sweep_parameters("axis2", V2_setpoints, "V", "Gate 2 biases")
# Add the custom sequence to the OPX
opx_instrument.qua_program = raster_scan(simulate=True)
# Simulate program
opx_instrument.sim_time(100_000)
opx_instrument.simulate()
opx_instrument.plot_simulated_wf()
# Execute program
opx_instrument.qua_program = raster_scan(simulate=False)
do0d(
    opx_instrument.run_exp,
    opx_instrument.resume,
    opx_instrument.get_measurement_parameter(),
    opx_instrument.halt,
    do_plot=True,
    exp=experiment,
)
