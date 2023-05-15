import os
import qcodes as qc
from qcodes import initialise_or_create_database_at, load_or_create_experiment
from qcodes.utils.dataset.doNd import do2d, do1d, do0d
from qcodes import Parameter
from qm.qua import *
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX
from configuration import *
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX, ResultParameters
from qm.qua import *
from typing import Dict
from qcodes.utils.validators import Numbers


# noinspection PyAbstractClass
class OPXCustomSequence(OPX):
    """
    Adaptation of the QCoDeS driver for the OPX for acquiring a charge stability map using a spiral scan.
    The driver was modified to adapt the reshaping and reordering of the data due to the spiral.
    """

    def __init__(
        self,
        config: Dict,
        name: str = "OPXCustomSequence",
        host=None,
        port=None,
        close_other_machines=True,
    ):
        super().__init__(
            config,
            name,
            host=host,
            port=port,
            close_other_machines=close_other_machines,
        )
        self.counter = 0

    @staticmethod
    def spiral(N: int):

        # casting to int if necessary
        if not isinstance(N, int):
            N = int(N)
        # asserting that N is odd
        N = N if N % 2 == 1 else N + 1

        # setting i, j to be in the middle of the image
        i, j = (N - 1) // 2, (N - 1) // 2

        # creating array to hold the ordering
        order = np.zeros(shape=(N, N), dtype=int)

        sign = +1  # the direction which to move along the respective axis
        number_of_moves = 1  # the number of moves needed for the current edge
        total_moves = 0  # the total number of moves completed so far

        # spiralling outwards along x edge then y
        while total_moves < N**2 - N:
            for _ in range(number_of_moves):
                i = i + sign  # move one step in left (sign = -1) or right (sign = +1)
                total_moves = total_moves + 1
                order[i, j] = total_moves  # updating the ordering array

            for _ in range(number_of_moves):
                j = j + sign  # move one step in down (sign = -1) or up (sign = +1)
                total_moves = total_moves + 1
                order[i, j] = total_moves
            sign = sign * -1  # the next moves will be in the opposite direction
            # the next edges will require one more step
            number_of_moves = number_of_moves + 1

        # filling the final x edge, which cannot cleanly be done in the above while loop
        for _ in range(number_of_moves - 1):
            i = i + sign  # move one step in left (sign = -1) or right (sign = +1)
            total_moves = total_moves + 1
            order[i, j] = total_moves

        return order

    def get_res(self):
        """
        Fetch the results from the OPX, convert it into Volts and cast it into a dict.
        :return: dict containing the fetched results.
        """

        if self.result_handles is None:
            return None
        else:
            output = {}
            for i in range(len(self.results["types"])):
                # Get data and convert to Volt
                out = None
                # demodulated or integrated data
                self.result_handles.get(self.results["names"][i]).wait_for_values(
                    self.counter
                )
                if self.results["types"][i] == "IQ":
                    out = (
                        -(
                            self.result_handles.get(self.results["names"][i]).fetch(
                                self.counter - 1
                            )["value"]
                        )
                        * 4096
                        / self.readout_pulse_length()
                    )
                # raw adc traces
                elif self.results["types"][i] == "adc":
                    out = (
                        -(
                            self.result_handles.get(self.results["names"][i]).fetch(
                                self.counter - 1
                            )["value"]
                        )
                        / 4096
                    )
                # Reshape data
                out = out.reshape(self.results["buffers"][i][0])
                output[self.results["names"][i]] = out[
                    self.spiral(int(np.sqrt(self.results["buffers"][i][0])))
                ]

            # Add amplitude and phase if I and Q are in the SP
            if "I" in output.keys() and "Q" in output.keys():
                output["R"] = np.sqrt(output["I"] ** 2 + output["Q"] ** 2)
                output["Phi"] = (
                    np.unwrap(np.angle(output["I"] + 1j * output["Q"])) * 180 / np.pi
                )
            return output

    def get_measurement_parameter(self):
        """
        Find the correct Parameter shape based on the stream-processing and return the measurement Parameter.
        :return: Qcodes measurement parameters.
        """

        # Reset the results in case the stream processing was changed between two iterations
        self.results = {"names": [], "types": [], "buffers": [], "units": []}

        # Add amplitude and phase if I and Q are in the SP
        if len(self.results["names"]) == 0:
            self._get_stream_processing(self.get_prog())

            if "I" in self.results["names"] and "Q" in self.results["names"]:
                self.results["names"].append("R")
                self.results["names"].append("Phi")
                self.results["units"].append("V")
                self.results["units"].append("rad")
            if "adc" in self.results["types"]:
                self.axis1_start(0)
                self.axis1_stop(int(self.readout_pulse_length()))
                self.axis1_step(1)
                self.axis1_npoints(int(self.readout_pulse_length()))
                self.axis1_axis.unit = "ns"
                self.axis1_axis.label = "Readout time"

            return ResultParameters(
                self,
                self.results["names"],
                "OPX_results",
                names=self.results["names"],
                units=self.results["units"],
                shapes=((self.results["buffers"][0][0], self.results["buffers"][0][0]),)
                * len(self.results["names"]),
                setpoints=((self.axis2_axis(), self.axis1_axis()),)
                * len(self.results["names"]),
                setpoint_units=((self.axis2_axis.unit, self.axis1_axis.unit),)
                * len(self.results["names"]),
                setpoint_labels=((self.axis2_axis.label, self.axis1_axis.label),)
                * len(self.results["names"]),
            )


def round_to_fixed(x, number_of_bits=12):
    """
    function which rounds 'x' to 'number_of_bits' of precision to help reduce the accumulation of fixed point arithmetic errors
    """
    return round((2**number_of_bits) * x) / (2**number_of_bits)


def measurement_macro(measured_element, I, I_stream, Q, Q_stream):
    measure(
        "readout",
        measured_element,
        None,
        integration.full("cos", I, "out1"),
        integration.full("cos", Q, "out2"),
    )
    save(I, I_stream)
    save(Q, Q_stream)


#####################################
#           Qcodes set-up           #
#####################################
db_name = "QM_demo.db"  # Database name
sample_name = "spiral"  # Sample name
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
opx_instrument = OPXCustomSequence(config, name="OPX", host="127.0.0.1")
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
#        spiral scan            #
#################################
Vx_center = 0.0
Vx_span = 0.2
Vy_center = 0.0
Vy_span = 0.1
N = 21
Vx_setpoints = np.linspace(Vx_center - Vx_span / 2, Vx_center + Vx_span / 2, N)
Vy_setpoints = np.linspace(Vy_center - Vy_span / 2, Vy_center + Vy_span / 2, N)
wait_time = 100
n_avg = 2000
# Check that the resolution is odd to form the spiral
assert N % 2 == 1, "the parameter 'N' must be odd {}".format(N)

# Get the gate pulse amplitude and derive the voltage step
pulse = config["elements"]["gate_1"]["operations"]["bias"]
wf = config["pulses"][pulse]["waveforms"]["single"]
V_step = config["waveforms"][wf].get("sample")
dx = round_to_fixed(Vx_span / ((N - 1) * config["waveforms"][wf].get("sample")))
dy = round_to_fixed(Vy_span / ((N - 1) * config["waveforms"][wf].get("sample")))


def spiral_scan(x_element, y_element, readout_element, simulate=False):
    with program() as prog:
        i = declare(int)  # an index variable for the x index
        j = declare(int)  # an index variable for the y index
        Vx = declare(fixed)  # a variable to keep track of the Vx coordinate
        Vy = declare(fixed)  # a variable to keep track of the Vy coordinate
        last_row = declare(bool)
        Vx_st = declare_stream()
        Vy_st = declare_stream()
        average = declare(int)  # an index variable for the average

        moves_per_edge = declare(int)  # the number of moves per edge [1, N]
        completed_moves = declare(int)  # the number of completed move [0, N ** 2]
        movement_direction = declare(fixed)  # which direction to move {-1., 1.}

        # declaring the measured variables and their streams
        I, Q = declare(fixed), declare(fixed)
        I_st, Q_st = declare_stream(), declare_stream()
        with infinite_loop_():
            if not simulate:
                pause()
            with for_(average, 0, average < n_avg, average + 1):
                # initialising variables
                assign(moves_per_edge, 1)
                assign(completed_moves, 0)
                assign(movement_direction, +1)
                assign(Vx, 0.0)
                assign(Vy, 0.0)
                assign(last_row, False)

                ramp_to_zero(x_element)
                ramp_to_zero(y_element)
                align(x_element, y_element, readout_element)
                # for the first pixel it is unnecessary to move before measuring
                measurement_macro(readout_element, I, I_st, Q, Q_st)
                save(Vx, Vx_st)
                save(Vy, Vy_st)

                with while_(completed_moves < N**2 - 1):
                    # for_ loop to move the required number of moves in the x direction
                    with for_(i, 0, i < moves_per_edge, i + 1):
                        assign(Vx, Vx + movement_direction * dx * V_step)
                        # if the x coordinate should be 0, ramp to zero to remove fixed point arithmetic errors accumulating
                        with if_(Vx == 0.0):
                            ramp_to_zero(x_element)
                        # playing the constant pulse to move to the next pixel
                        with else_():
                            play("bias" * amp(movement_direction * dx), x_element)
                        # Make sure that we measure after the pulse has settled
                        align(x_element, y_element, readout_element)
                        # if logic to enable wait_time = 0 without error
                        if wait_time >= 4:
                            wait(wait_time // 4, readout_element)
                        # Measurement
                        measurement_macro(readout_element, I, I_st, Q, Q_st)
                        save(Vx, Vx_st)
                        save(Vy, Vy_st)
                    # for_ loop to move in the y direction except for the last step which is only along x
                    with if_(~last_row):
                        with for_(j, 0, j < moves_per_edge, j + 1):
                            assign(Vy, Vy + movement_direction * dy * V_step)
                            # if the y coordinate should be 0, ramp to zero to remove fixed point arithmetic errors accumulating
                            with if_(Vy == 0.0):
                                ramp_to_zero(y_element)
                            # playing the constant pulse to move to the next pixel
                            with else_():
                                play("bias" * amp(movement_direction * dy), y_element)
                            # Make sure that we measure after the pulse has settled
                            align(x_element, y_element, readout_element)
                            # if logic to enable wait_time = 0 without error
                            if wait_time >= 4:
                                wait(wait_time // 4, readout_element)
                            # Measurement
                            measurement_macro(readout_element, I, I_st, Q, Q_st)
                            save(Vx, Vx_st)
                            save(Vy, Vy_st)
                        # updating the variables
                        # * 2 because moves in both x and y
                        assign(completed_moves, completed_moves + 2 * moves_per_edge)
                        # *-1 as subsequent steps in the opposite direction
                        assign(movement_direction, movement_direction * -1)
                        # moving one row/column out so need one more move_per_edge except for the last step which is N-1
                        with if_(moves_per_edge < N - 1):
                            assign(moves_per_edge, moves_per_edge + 1)
                        with else_():
                            assign(last_row, True)
                    with else_():
                        # updating the variables
                        # * 1 because moves only along x
                        assign(completed_moves, completed_moves + moves_per_edge)

                # aligning and ramping to zero to return to initial state
                align(x_element, y_element, readout_element)
                ramp_to_zero(x_element)
                ramp_to_zero(y_element)

        with stream_processing():
            Vx_st.buffer(N**2).buffer(n_avg).map(FUNCTIONS.average()).save_all("I")
            Vy_st.buffer(N**2).buffer(n_avg).map(FUNCTIONS.average()).save_all("Q")
    return prog


# Axis1 is the most inner loop
opx_instrument.set_sweep_parameters("axis1", Vy_setpoints, "V", "Gate 2 biases")
# Axis2 is the second loop
opx_instrument.set_sweep_parameters("axis2", Vx_setpoints, "V", "Gate 1 biases")
# Add the custom sequence to the OPX
opx_instrument.qua_program = spiral_scan(
    "gate_1", "gate_2", "readout_element", simulate=True
)
# Simulate program
opx_instrument.sim_time(100_000)
# opx_instrument.simulate()
# opx_instrument.plot_simulated_wf()
# Execute program
# Set the dc offset to the center of the spiral (these must be set to the slow voltage source)
# qm.set_output_dc_offset_by_element("gate_2", "single", Vy_center())
# qm.set_output_dc_offset_by_element("gate_1", "single", Vx_center())
opx_instrument.qua_program = spiral_scan(
    "gate_1", "gate_2", "readout_element", simulate=False
)
do0d(
    opx_instrument.run_exp,
    opx_instrument.resume,
    opx_instrument.get_measurement_parameter(),
    opx_instrument.halt,
    do_plot=True,
    exp=experiment,
)
# Can also use do1d and do2d to perform a wide stability diagram by scanning the external DC voltages
# do1d(
#     VP1,
#     10,
#     20,
#     10,
#     0.1,
#     opx_instrument.resume,
#     opx_instrument.get_measurement_parameter(),
#     enter_actions=[opx_instrument.run_exp],
#     exit_actions=[opx_instrument.halt],
#     show_progress=True,
#     do_plot=True,
#     exp=experiment,
# )

# do2d(
#     VP1,
#     -5,
#     5,
#     11,
#     0.1,
#     VP2,
#     10,
#     20,
#     7,
#     0.1,
#     opx_instrument.resume,
#     opx_instrument.get_measurement_parameter(),
#     enter_actions=[opx_instrument.run_exp],
#     exit_actions=[opx_instrument.halt],
#     show_progress=True,
#     do_plot=True,
#     exp=experiment,
# )
