# Basic QCoDeS driver usage example

This section will show you how to incorporate the OPX into your QCoDeS environment using the 
[basic OPX driver](https://github.com/qua-platform/py-qua-tools/tree/main/qualang_tools/external_frameworks/qcodes).
It contains two files:
* [configuration.py](configuration.py): the example configuration file used in hello_qcodes.py.
* [hello_qcodes.py](hello_qcodes.py): the example file showing the basic driver usage.

The main structure can be divided in four sections that will be detailed below:
```python
###########################
#     IMPORT SECTION     #
###########################
# QCoDeS, QUA and Python packages
import os
import qcodes as qc
from qm.qua import *
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX
from configuration import *
# ...

#######################################
#      QCoDeS environment set-up      #
#######################################
# Initialize the QCoDeS station to which instruments will be added
station = qc.Station()
# Create the OPX instrument class
opx_instrument = OPX(config, name="OPX_demo", host=qop_ip)
# Add the OPX instrument to the QCoDeS station
station.add_component(opx_instrument)

##############################################
#      OPX experimental sequence set-up      #
##############################################
# Pass the readout length (in ns) to the class to convert the demodulated/integrated data into Volts
# and create the setpoint Parameter for raw adc trace acquisition
opx_instrument.readout_pulse_length(readout_len)
# Function returning the QUA program
def opx_instrument(simulate=False):
    with program() as prog:
        # Variable declaration
        I = declare(fixed) 
        I_st = declare_stream()
        # ...
        # Infinite loop starting with a pause() statement
        with infinite_loop_():
            if not simulate:
                pause()
            # The pulse sequence
            play('cw', 'qubit') 
            # ...
        # The stream processing
        with stream_processing():
            I_st.buffer(...).average().save_all('I') 
            # ...
    return prog

#############################################
#      Program simulation or execution      #
#############################################
# Simulate the program
opx_instrument.qua_program = opx_instrument(simulate=True)
opx_instrument.sim_time(10_000)
opx_instrument.simulate()
opx_instrument.plot_simulated_wf()

# Execute the program using do0d, do1d or do2d
opx_instrument.qua_program = OPX_0d_scan(simulate=False)
do0d(
    opx_instrument.run_exp,
    opx_instrument.resume,
    opx_instrument.get_measurement_parameter(),
    opx_instrument.halt,
    do_plot=True,
    exp=experiment,
)
```

## 1. Import section
Standard import section containing your Python, QCoDeS and QUA packages. 

In order to use the driver, you just need to update the qualang-tool package and add the line: 
``from qualang_tools.external_frameworks.qcodes.opx_driver import OPX``.

## 2. QCoDeS environment set-up
This section is dedicated to setting-up the QCoDeS framework. The structure provided in hello_qcodes.py is just given
as an example and you can replace it with your own way of doing.

In order to incorporate the OPX into your existing framework, you just need to create the OPX instrument class and add it to your station:
```python
opx_instrument = OPX(config=config, name="OPX_demo", host="127.0.0.1", port=80)
station.add_component(opx_instrument)
```

## 3. OPX experimental sequence set-up
In this section, you will need to write the QUA program corresponding to the pulse sequence to be played by the OPX.

### The QUA program
As shown in the example file, the QUA pulse sequence must be written under and infinite loop starting with a ``pause()`` command.
This is needed to synchronize the OPX sequence with possible external parameter sweeps performed by QCoDeS using do1d and do2d.
As explained in the next section, each iteration of the QCoDes scan starts by calling the ``resume`` function that unpauses the OPX program.

Similarly, in order to be sure that we fetch the results corresponding to each iteration of the QCoDeS sweep, it is necessary to use the ``save_all()`` command in the stream_processing.
Indeed, this way we can use a counter to keep track of the fetched data and ensure that we always fetch the latest one to feed the measurement Parameters.

The QUA program can either be written directly using the ``with program() as prog:`` context manager, as in
```python
with program() as prog:
    ...
return prog
# Add the QUA program to the OPX
opx_instrument.qua_program = prog
```

or embedded in a function that would allow more parametrization as in:
```python
def OPX_custom_scan(param1, param2, ...):
    with program() as prog:
        ...
    return prog
# Add the QUA program to the OPX
opx_instrument.qua_program = OPX_custom_scan(param1= , param2= , ...)
```

In the examples contained in hello_qcodes.py, the second method is preferred so that a flag called ``simulate`` can 
be passed to the function to remove the ``pause()`` command when the user wants to simulate the QUA program.
```python
def OPX_0d_scan(simulate=False):
    with program() as prog:
        I = declare(fixed)
        Q = declare(fixed)
        Q_st = declare_stream()
        I_st = declare_stream()
        with infinite_loop_():
            if not simulate:
                pause()
            measure(
                "readout",
                "readout_element",
                None,
                integration.full("cos", I, "out1"),
                integration.full("cos", Q, "out2"),
            )
            save(I, I_st)
            save(Q, Q_st)

        with stream_processing():
            I_st.save_all("I")
            Q_st.save_all("Q")
    return prog
# Add the custom sequence to the OPX for simulation
opx_instrument.qua_program = OPX_0d_scan(simulate=True)
```

### The readout length
In order to convert the demodulated/integrated results into Volts, and create the setpoints for the raw ADC trace acquisition, 
the readout length (in nanoseconds) must be passed to the instrument with ``opx_instrument.readout_pulse_length(readout_len)``.

Note that this doesn't update the effective readout length, it is just a ``get`` parameter.
As shown in the advanced driver section, it is possible to modify the class in order to parametrize the readout length and amplitude.

## 4. Program simulation or execution
This last section is dedicated to simulating or executing the QUA program.

### Program simulation
In order to simulate the QUA program, the ``pause()`` command must be removed otherwise no pulse will be played.

After defining how long (in nanoseconds) will the program be simulated using the ``sim_time()`` parameter, 
you can start the simulation with the ``simulate()`` function. At the end, the simulated waveforms will be stored in the 
``simulated_wf`` attribute of the OPX instrument. The simulated waveforms can also be plotted using the ``plot_simulated_wf()`` function as in: 
```python
# Add the custom sequence to the OPX
opx_instrument.qua_program = OPX_0d_scan(simulate=True)
# Simulate program
opx_instrument.sim_time(10_000)
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
