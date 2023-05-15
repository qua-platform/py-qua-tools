# QCoDeS drivers

This subpackage contains drivers to set the OPX as a QCoDeS instrument and synchronize external parameter sweeps with 
sequences running on the OPX using the QCoDeS do"nd" methods. 
Since the OPX runs on a unique pulse processor, it can perform complex sequences that QCoDeS do not natively support. 
For example, acquire data with different formats and sweep parameters on his own.
To more fully support the OPX capabilities, this driver is more complex compared to other QCoDeS instruments' drivers.

This package provides tested and ready-to-use drivers and you will find in the 
[examples/Qcodes_drivers](https://github.com/qua-platform/py-qua-tools/tree/main/examples/Qcodes_drivers) section
a guide on how to customize the present drivers to better suit your experiments and your way of working with the OPX.

## [Main opx driver](opx_driver.py)

This is where the OPX is defined as a QCoDeS instrument. 
This file contains several other classes to describe the results acquired with the OPX as QCoDeS parameters as well as setpoint parameters.

### OPX
Python class inheriting from the QCoDeS `Instrument` and defining the OPX main driver. 
It contains the methods to enable the connection with the OPX by opening a quantum machine manager, update the configuration,
open a quantum machine, simulate, compile and execute QUA programs.

* ``connect_to_qmm(host, port)``: Enable the connection with the OPX by creating the QuantumMachineManager.
* ``get_din()``: Parse a standard VISA *IDN? response into an ID dict.
* ``connect_message()``: Print a standard message on initial connection to an instrument.
* ``set_config(config)``: Update the configuration used by the OPX.
* ``open_qm()``: Open a quantum machine with a given configuration ready to execute a program.
* ``get_prog()``: Get the implemented QUA program.
* ``get_res()``: Get the results from the OPX.
* ``set_sweep_parameters(scanned_axis, setpoints, unit=None, label=None)``: Set the setpoints based on the sweep parameters.
* ``get_measurement_parameter()``: Find the correct Parameter shape based on the stream-processing and return the measurement Parameter. If 'I' and 'Q' are saved in the stream_processing, then the amplitude 'R' and phase 'Phi' will also be returned.
* ``execute_prog(prog)``: Execute a given QUA program and creates a result handle to fetch the results.
* ``compile_prog(prog)``: Compile a given QUA program and stores it under the prog_id attribute.
* ``execute_compiled_prog()``: Add a compiled program to the current queue and create a result handle to fetch the results.
* ``simulate_prog(prog)``: Simulate a given QUA program and store the simulated waveform into the simulated_wf attribute.
* ``plot_simulated_wf()``: Plot the simulated waveforms in a new figure using matplotlib.
* ``halt()``: Interrupt the current job and halt the running program.
* ``close()``: Close the quantum machine and tear down the OPX instrument.

### Results parameters 
Subclass of the QCoDeS ``MultiParameter`` class used to define the shapes, setpoints and get_raw() attributes of 
specific measurement modes of the OPX as defined in QUA program and Stream Processing.

### SetPoint classes

Classes inheriting from the QCoDeS ``Parameter`` class and used to defined the setpoints of the parameter scans performed with QCoDeS.

* ``GeneratedSetPoints``: A parameter that generates a setpoint array parametrized with start, stop and number of points.
* ``GeneratedSetPointsSpan``: A parameter that generates a setpoint array parametrized span, center and number of points.


## Usage

When integrating the OPX in your QCoDeS framework, there are a few critical points to pay attention to:
* In the QUA program, always insert the pulse sequence under an infinite loop starting with a ``pause()`` command. This is needed to synchronize the OPX sequence with the QCoDeS parameters sweep.
* In the QUA program, in the stream processing, make sure to save the results with the ``save_all()`` command. This is needed to synchronize the OPX sequence with the QCoDeS parameters sweep.
* In the do'n'd method, make sure to always call ``run_exp`` at the beginning to send the QUA program to the OPX, `resume` at each iteration to start the OPX pulse sequence, `get_measurement_parameter()` to define the QCoDeS measurement parameters for this experiment and ``halt`` at the end to close the job.
* Make sure to define the setpoint parameters for the OPX scanned axes using ``set_sweep_parameters()``. Note that "axis1" is the most inner loop and "axis2" is the second loop.

The code block below shows the basic structure for running an experiment with the OPX integrated in the QCoDeS framework.

```python
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX
import os
import qcodes as qc
from qcodes import initialise_or_create_database_at, load_or_create_experiment
from qcodes.utils.dataset.doNd import do2d, do1d, do0d
from qcodes import Parameter
from qm.qua import *
from configuration import *

#####################################
#           QCoDeS set-up           #
#####################################
db_name = "QM_demo.db"  # Database name
sample_name = "demo"  # Sample name
exp_name = "OPX_qcodes_drivers"  # Experiment name

# Initialize QCoDeS database
db_file_path = os.path.join(os.getcwd(), db_name)
qc.config.core.db_location = db_file_path
initialise_or_create_database_at(db_file_path)
# Initialize QCoDeS experiment
experiment = load_or_create_experiment(
    experiment_name=exp_name, sample_name=sample_name
)
# Initialize the QCoDeS station to which instruments will be added
station = qc.Station()
# Create the OPX instrument class
opx_pulse_sequence = OPX(config, name="OPX_demo", host="127.0.0.1")
# Add the OPX instrument to the QCoDeS station
station.add_component(opx_pulse_sequence)

#####################################
#        2D SWEEP & do0d            #
#####################################
gate_1_step = 0.01
gate_1_biases = np.arange(-0.2, 0.2, gate_1_step)
gate_1_prefactor = gate_1_step / gate_1_amp

gate_2_step = 0.01
gate_2_biases = np.arange(0, 0.25, gate_2_step)
gate_2_prefactor = gate_2_step / gate_2_amp
def OPX_2d_scan(simulate=False):
    with program() as prog:
        i = declare(int)
        j = declare(int)
        I = declare(fixed)
        Q = declare(fixed)
        I_st = declare_stream()
        Q_st = declare_stream()
        with infinite_loop_():
            if not simulate:
                pause()
            with for_(i, 0, i < len(gate_1_biases), i + 1):
                with if_(i == 0):
                    play("bias" * amp(0), "gate_1")
                with else_():
                    play("bias" * amp(gate_1_prefactor), "gate_1")

                with for_(j, 0, j < len(gate_2_biases), j + 1):
                    with if_(j == 0):
                        play("bias" * amp(0), "gate_2")
                    with else_():
                        play("bias" * amp(gate_2_prefactor), "gate_2")

                    wait(200 // 4, "readout_element")
                    measure("readout", "readout_element", None,
                            integration.full("cos", I, "out1"),
                            integration.full("cos", Q, "out2"))
                    save(I, I_st)
                    save(Q, Q_st)

                ramp_to_zero("gate_2")
            ramp_to_zero("gate_1")

        with stream_processing():
            I_st.buffer(len(gate_2_biases)).buffer(len(gate_1_biases)).save_all("I")
            Q_st.buffer(len(gate_2_biases)).buffer(len(gate_1_biases)).save_all("Q")
    return prog

# Parametrize the OPX readout scheme
opx_pulse_sequence.readout_pulse_length(readout_len)  # Set the readout duration in ns
# Axis1 is the most inner loop
opx_pulse_sequence.set_sweep_parameters("axis1", gate_2_biases, "V", "Gate 2 biases")
# Axis2 is the second loop
opx_pulse_sequence.set_sweep_parameters("axis2", gate_1_biases, "V", "Gate 1 biases")
# Add the custom sequence to the OPX
opx_pulse_sequence.qua_program = OPX_2d_scan(simulate=True)
# Simulate program
opx_pulse_sequence.sim_time(100_000)
opx_pulse_sequence.simulate()
opx_pulse_sequence.plot_simulated_wf()
# Execute program
opx_pulse_sequence.qua_program = OPX_2d_scan(simulate=False)
do0d(
    opx_pulse_sequence.run_exp,
    opx_pulse_sequence.resume,
    opx_pulse_sequence.get_full_data(),
    do_plot=True,
    exp=experiment
)
```

More details and advices to create your own experiment driver can be found in the examples section: 
https://github.com/qua-platform/py-qua-tools/tree/main/examples/Qcodes_drivers 