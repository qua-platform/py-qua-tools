# Octave Tools
This library includes tools to improve the users Octave experience.

## get_calibration_parameters_from_db
This function will look into the calibration database and return the correction parameters (offsets and correction 
matrix) corresponding to a given set of intermediate frequency, Octave LO frequency and gain. 

The correction parameters are returned in the format of a dictionary:
```
{'offsets': {'I': I_offset, 'Q': Q_offset},
 'correction_matrix': (c00, c01, c10, c11)}
```

If no calibration parameters are found in the database, the function will either:
* return the dictionary with empty values (verbose_level 0)
* return the dictionary with empty values and print a warning in the Python console (verbose_level 1)
* raise an error and block the execution of the script (verbose_level 2)


### Usage example
 
```python
from qualang_tools.octave_tools import get_calibration_parameters_from_db

# Open the qmm and qm
qmm = QuantumMachinesManager()
qm = qmm.open_qm(config)

# Calibrate the desired set of LO frequency and IF
qm.octave.set_rf_output_gain("qubit", -7)
qm.calibrate_element("qubit", {5e9: (50e6,)})

# Set the new frequency with calibrated gain
qm.octave.set_lo_frequency("qubit", 5e9)
qm.octave.set_rf_output_gain("qubit", -7)
# Get the correction parameters corresponding to the desired parameters:
param_qubit = get_calibration_parameters_from_db(
    path_to_database="", config=config, element="qubit", 
    LO=5e9, IF=50e6, gain=-7, 
    verbose_level=1)
```

## set_correction_parameters_to_opx
This function will look into the calibration database and update the correction parameters in Python, (offsets and 
correction matrix) corresponding to a given set of intermediate frequency, Octave LO frequency and gain. 

The goal to give the user the ability to easily update the correction parameters while sweeping the LO frequency
in Python for instance.

The correction parameters are returned in the format of a dictionary:
```
{'offsets': {'I': I_offset, 'Q': Q_offset},
 'correction_matrix': (c00, c01, c10, c11)}
```

If no calibration parameters are found in the database, the function will either:
* not update the parameters and return the dictionary with empty values (verbose_level 0)
* not update the parameters, return the dictionary with empty values and print a warning in the Python console (verbose_level 1)
* raise an error and block the execution of the script (verbose_level 2)

### Usage example

```python
from qualang_tools.octave_tools import set_correction_parameters_to_opx

with program() as LO_sweep_prog:
    # QUA declarations
    ...
    with for_(i, 0, i < len(lo_frequencies) + 1, i + 1):
        pause()  # This waits until it is resumed from python
        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f, frequencies)):
                # Update the frequency of the digital oscillator linked to the qubit element
                update_frequency("qubit", f)
                # Play the pulse
                ...

# Open the QMM
qmm = QuantumMachinesManager()
# Open the quantum machine
qm = qmm.open_qm(config)
# Set the Octave gain
qm.octave.set_rf_output_gain("qubit", 0)
# Loop over the LO frequencies
for i in range(len(lo_frequencies)):  
    # Set the frequency and gain of the LO source
    qm.octave.set_lo_frequency("qubit", lo_frequencies[i])
    # Update the correction parameters
    set_correction_parameters_to_opx(
        path_to_database="",
        config=config,
        element="qubit",
        LO=freqs_external[i],
        IF=IFs[0],
        gain=0,
        qm=qm,
    )
    # Resume the QUA program (escape the 'pause' statement)
    job.resume()
    # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
    wait_until_job_is_paused(job)
    # Fetch the results from the OPX
    ...
```

## get_correction_for_each_LO_and_IF
Look in the calibration database for the calibration parameters corresponding to the provided set of LO
frequencies, intermediate frequencies and gain.
The intermediate frequencies considered here are only the ```nb_of_updates``` equally spaced frequencies from the
provided ```IF_list```. For instance, if a list of 100 intermediate frequencies is provided, but nb_of_update is set
    to 10, then only 10 correction parameters will be returned for the returned equally spaced intermediate frequencies.

The goal is to perform a wide frequency sweep (scan the LO frequency in Python and the IF in QUA) and update the
mixer correction parameters for each LO frequency and a few intermediate frequencies, given by ```nb_of_updates```, 
in QUA.

If the flag ```calibrate``` is set to True (the opened Quantum Machine needs to be provided), then the specified element will be calibrated at the given frequencies
(all LO frequencies and only the ``nb_of_updates``` intermediate frequencies).

The function will return the list on intermediate frequencies at which the correction matrix will be updated in the
program (```nb_of_updates``` items) and the four coefficients of the correction matrix and two offsets with one element for each pair (LO, IF) (```nb_of_updates * len(LO_list)``` items).

### Usage example

```python
from qualang_tools.octave_tools import get_correction_for_each_LO_and_IF

# Open the QMM
qmm = QuantumMachinesManager()
# Open the quantum machine
qm = qmm.open_qm(config)

# The intermediate frequency sweep parameters
f_min = 1e6
f_max = 251e6
df = 1e6
intermediate_frequencies = np.arange(f_min, f_max + 0.1, df)
# The LO frequency sweep parameters
f_min_external = 5.001e9 - f_min
f_max_external = 5.5e9 - f_max
df_external = f_max - f_min
lo_frequencies = np.arange(f_min_external, f_max_external + df_external / 2, df_external)

# Get the list of intermediate frequencies at which the correction matrix will 
# be updated in QUA and the corresponding correction matrix elements
IFs, c00, c01, c10, c11, offset_I, offset_Q = get_correction_for_each_LO_and_IF(
    path_to_database="",
    config=config,
    element="qubit",
    gain=0,
    LO_list=lo_frequencies,
    IF_list=intermediate_frequencies,
    nb_of_updates=5,
    calibrate=True,
    qm=qm,
)

with program() as LO_sweep_prog:
    # QUA declarations
    c00_qua = declare(fixed, value=c00)
    c01_qua = declare(fixed, value=c01)
    c10_qua = declare(fixed, value=c10)
    c11_qua = declare(fixed, value=c11)
    offset_I_qua = declare(fixed, value=offset_I)
    offset_Q_qua = declare(fixed, value=offset_Q)
    ...
    with for_(i, 0, i < len(lo_frequencies) + 1, i + 1):
        pause()  # This waits until it is resumed from python
        set_dc_offset("qubit", "I", offset_I_qua[i])
        set_dc_offset("qubit", "Q", offset_Q_qua[i])
        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f, intermediate_frequencies)):
                # Update the frequency of the digital oscillator linked to the qubit element
                update_frequency("qubit", f)
                # Update the correction matrix only at a pre-defined set of intermediate frequencies
                with switch_(f):
                    for idx, current_if in enumerate(IFs):
                        with case_(int(current_if)):
                            update_correction(
                                "qubit",
                                c00_qua[len(IFs) * i + idx],
                                c01_qua[len(IFs) * i + idx],
                                c10_qua[len(IFs) * i + idx],
                                c11_qua[len(IFs) * i + idx],
                            )
                # Play the pulse
                ...
                
# Loop over the LO frequencies
for i in range(len(lo_frequencies)):  
    # Set the frequency and gain of the LO source
    qm.octave.set_lo_frequency("qubit", lo_frequencies[i])
    # Resume the QUA program (escape the 'pause' statement)
    job.resume()
    # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
    wait_until_job_is_paused(job)
    # Fetch the results from the OPX
    ...
```

## calibrate_several_frequencies
Calibrate a given element for a set of LO and intermediate frequencies. 
Each set of correction parameters will be saved in the calibration database.

### Usage example

```python
from qualang_tools.octave_tools import octave_calibration_tool

# Open the QMM
qmm = QuantumMachinesManager()
# Open the quantum machine
qm = qmm.open_qm(config)

# The intermediate frequency sweep parameters
f_min = 1e6
f_max = 251e6
df = 1e6
intermediate_frequencies = np.arange(f_min, f_max + 0.1, df)
# The LO frequency sweep parameters
f_min_external = 5.001e9 - f_min
f_max_external = 5.5e9 - f_max
df_external = f_max - f_min
lo_frequencies = np.arange(f_min_external, f_max_external + df_external / 2, df_external)

# Calibrate all the desired frequencies
octave_calibration_tool(
    qm,
    element="qubit",
    lo_frequencies=lo_frequencies,
    intermediate_frequencies=intermediate_frequencies
)
```
