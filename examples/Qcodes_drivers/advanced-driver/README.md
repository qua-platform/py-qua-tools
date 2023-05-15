# Advanced QCoDeS driver usage example

This section will show you how to modify the existing [OPX driver](https://github.com/qua-platform/py-qua-tools/tree/main/qualang_tools/external_frameworks/qcodes) and incorporate it into your QCoDeS environment using the 
.
It contains three files:
* [configuration.py](configuration.py): the example configuration file used in hello_qcodes.py.
* [hello_qcodes_advanced.py](hello_qcodes_advanced.py): the example file showing the basic driver usage.
* [advanced_driver.py](advanced_driver.py): the modified OPX QCoDeS driver.


## How to customize the OPX QCoDeS driver

The file [advanced_driver.py](advanced_driver.py) shows you how to create a modified driver, that inherits from the OPX instrument class defined [here](https://github.com/qua-platform/py-qua-tools/tree/main/qualang_tools/external_frameworks/qcodes),
to better suit your experiment and the way you want to interact with the OPX.

In the example shown here, we modified the basic driver to incorporate everything related to the measurement performed by the OPX (variable declaration, measure statement and stream_processing) inside the class.
This lightens the QUA programs and allows parametrization of the measurement (readout element, operation, length and amplitude).
One drawback is that it "hides" the measurement and prevents you from scanning the readout parameters in realtime.

To this purpose, Parameters and methods can be added or modified with respect to the main OPX class and the following sections will show you how this has been done for this specific example.

### 1. Add Parameters
On top of the Parameters already defined in the main OPX class, we added several new Parameters to further customize the class:
* __readout_element__: the readout element which must be defined in the config. 
* __readout_operation__: the readout operation which must be defined in the config.
* __readout_pulse_amplitude__: the readout amplitude in V.
* __acquisition_mode__: that defines the operations performed by the measure() statement. Can be 'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'.
* __slice_size__: length of one slice (in clock cycles) when using sliced integration or sliced demodulation.
* __wait_for_trigger__: flag allowing to trigger the OPX pulse sequence using and external signal.
* __opx_scan__: defines the dimension of the parameter sweep performed by the OPX and used to construct the stream_processing. Can be '0d', '1d' or '2d'.
* __outer_averaging_loop__: flag specifying if the averaging loop is the most outer loop or if it is located between the two swept parameter loops in the case of a two-dimensional scan.
* __n_avg__: number of averages used to construct the stream processing.
* __simulation__: flag to remove the ``pause()`` statement when simulating the QUA program.

These Parameters will then be used in the new methods defined below.

### 2. Add methods
In order to customize the driver, several methods and QUA macros have been added:
* __update_readout_parameters__: method to update the readout parameters (element, operation, duration and amplitude) based on the new Parameters.
* __measurement_declaration__: QUA macro used to declare the relevant QUA variables related to the measurement and based on ``acquisition_mode``. 
* __measurement__: QUA macro containing the measure statement based on ``acquisition_mode`` and ``opx_scan``.
* __stream_results__: QUA macro constructing the stream_processing based on ``acquisition_mode``, ``opx_scan`` and ``outer_averaging_loop``.
* __pulse_sequence__: method that will be replaced by the pulse sequence to be played by the OPX.

All these methods and macros can then be incorporated in the ``get_prog`` function.
### 3. Modify existing methods
In order to use these new methods, the ``get_prog`` function needs to be modified in order to update the readout parameters
and return the QUA program customized with the previously described QUA macros.
```python
def get_prog(self):
    # Update the readout duration and the integration weights
    self.update_readout_parameters()

    with program() as prog:
        # Declare the measurement variables (I, Q, I_st...)
        self.measurement_variables = self.measurement_declaration()
        # Infinite loop and pause() to synchronize with qcodes scans when we are not simulating
        with infinite_loop_():
            if not self.simulation():
                pause()
            # Wait for the AWG trigger if needed
            if self.wait_for_trigger():
                wait_for_trigger(self.readout_element())
                align()
            # Play a custom sequence with the OPX
            self.pulse_sequence(self)

        with stream_processing():
            # Transfer the results from the FPGA to the CPU
            self.stream_results()
    return prog
```
Note that with this driver, only the pulse sequence needs to be inputted by the user. The context manager, infinite loop and stream processing are already defined within the driver.

## Usage example of this advanced driver

The structure is essentially the same as described in the [basic-driver](../basic-driver) section.

## 1. Import section
Standard import section containing your Python, QCoDeS and QUA packages. 

In order to use the advanced driver, you just need to place the file in the current directory and add the line: 
``from advanced_driver import OPXCustomSequence``.

## 2. QCoDeS environment set-up
This section is dedicated to setting-up the QCoDeS framework. The structure provided in hello_qcodes_advanced.py is just given
as an example and you can replace it with your own way of doing.

In order to incorporate the OPX into your existing framework, you just need to create the OPX instrument class and add it to your station:
```python
opx_instrument = OPXCustomSequence(config=config, name="OPX_demo", host="127.0.0.1", port=80)
station.add_component(opx_instrument)
```

## 3. OPX experimental sequence set-up
In this section, you will need to write the QUA program corresponding to the pulse sequence to be played by the OPX and 
parametrize the driver according to the desired measurement scheme.

### The QUA program
Since the context manager ``with program() as prog:`` is already defined within the driver, you only need to write the desired pulse sequence as in:

```python
n_avg = 100
amp_vec = np.arange(0, 1.9, 0.02)
# QUA sequence
def custom_sequence(self):
    n = declare(int)
    a = declare(fixed)
    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(a, amp_vec)):
            play("cw" * amp(a), "qubit")
            self.measurement()
            align()
            wait(10_000, "qubit")
```
Note that the measurement is set with the line ``self.measurement()``, so it is important to have the pulse sequence embedded within a function defined with a single input argument called `self`.

### The driver parameters
The driver Parameters must now be defined according to the measurement scheme and pulse sequence provided above.
#### Readout scheme
```python
# Parametrize the OPX readout scheme. The config will be updated locally.
opx_instrument.readout_element("resonator")  # Set the readout element
opx_instrument.readout_operation("readout")  # Set the readout operation
opx_instrument.readout_pulse_length(1_000)  # Set the readout duration in ns
opx_instrument.readout_pulse_amplitude(0.01)  # Set the readout amplitude in V
# 'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'
opx_instrument.acquisition_mode("full_demodulation")
```

#### Scanned parameters
```python
# Dimension of the sweeps performed by the OPX. Can be '0d', '1d' or '2d'
opx_instrument.opx_scan("1d")
# Position of the averaging loop in a 2d OPX scan. False means that the averaging loop happens between axis1 and axis2.
opx_instrument.outer_averaging_loop(True)
opx_instrument.n_avg(n_avg)
# Setpoint of axis1 which is the most inner loop
opx_instrument.set_sweep_parameters(
    "axis1",
    amp_vec * config["waveforms"]["const_wf"]["sample"],
    "V",
    "pulse amplitude",
)
```
#### The pulse sequence and execution mode
```python
# Add the custom sequence to the OPX
opx_instrument.pulse_sequence = custom_sequence
# Specific mode for which the OPX executes its pulse sequence when a trigger is received.
opx_instrument.wait_for_trigger(False)
# OPX simulation mode
opx_instrument.simulation(True)
opx_instrument.sim_time(11_000)  # Simulation duration in ns
```
## 4. Program simulation or execution
The program simulation or execution follows the same rules as for the basic driver.

### Program simulation
Setting the simulation ``parameter`` to True will remove the ``pause()`` command so that the pulse sequence can be simulated.

After defining how long (in nanoseconds) will the program be simulated using the ``sim_time()`` parameter, 
you can start the simulation with the ``simulate()`` function. At the end, the simulated waveforms will be stored in the 
``simulated_wf`` attribute of the OPX instrument. The simulated waveforms can also be plotted using the ``plot_simulated_wf()`` function as in: 
```python
# OPX simulation mode
opx_instrument.simulation(True)
opx_instrument.sim_time(11_000)  # Simulation duration in ns
opx_instrument.simulate()
opx_instrument.plot_simulated_wf()
```
### Program execution
In order to execute the QUA program using the do'n'd methods, several steps are required.
1. The first command, or ``enter_actions`` must be ``run_exp`` to send the program to the OPX and initialize the result handle.
2. The last command, or ``exit_actions`` must be ``halt`` to exit the infinite loop and stop the QUA program.
3. At each QCoDeS iteration, the ``resume`` command must be called to pass the ``pause()`` statement and execute the pulse sequence.
4. The measurement parameters must be defined by calling the ``get_measurement_parameter()`` function as a QCoDeS ``*param_meas``. Note that the measurement parameters are automatically defined from the stream_processing.


You will find below the examples of calling do0d, do1d and do2d with fake external parameters VP1 and VP2.
```python
# do0d
do0d(
    opx_instrument.run_exp,
    opx_instrument.resume,
    opx_instrument.get_measurement_parameter(),
    opx_instrument.halt,
    do_plot=True,
    exp=experiment,
)
# do1d
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
# do2d
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
```
