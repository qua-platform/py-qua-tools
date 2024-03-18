# Octave Tools
This library includes tools to improve the users Octave experience.

**Note that these functions only work with `qm-qua >= 1.1.5`.**

## get_calibration_parameters
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
from qualang_tools.octave_tools import set_correction_parameters

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
param_qubit = set_correction_parameters(
    path_to_database="", config=config, element="qubit", 
    LO=5e9, IF=50e6, gain=-7, 
    qm=qm, verbose_level=1)
```

## set_correction_parameters
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
* return the dictionary with empty values (verbose_level 0)
* return the dictionary with empty values and print a warning in the Python console (verbose_level 1)
* raise an error and block the execution of the script (verbose_level 2)

### Usage example

```python
from qualang_tools.octave_tools import set_correction_parameters

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
# Loop over the LO frequencies
for i in range(len(lo_frequencies)):  
    # Set the frequency and gain of the LO source
    qm.octave.set_lo_frequency("qubit", lo_frequencies[i])
    qm.octave.set_rf_output_gain("qubit", 0)
    # Update the correction parameters
    set_correction_parameters(
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

## update_correction_for_each_IF
Look in the calibration database for the calibration parameters corresponding to the provided set of LO
frequencies, intermediate frequencies and gain.
The intermediate frequencies considered here are only the ```nb_of_updates``` equally spaced frequencies from the
provided ```IF_list```.

The goal is to perform a wide frequency sweep (scan the LO frequency in Python and the IF in QUA) and update the
mixer correction parameters for each LO frequency and a few intermediate frequencies, given by ```nb_of_updates```, 
in QUA.

If the flag ```calibrate``` is set to True (the opened Quantum Machine needs to be provided), then the specified element will be calibrated at the given frequencies
(all LO frequencies and only the ``nb_of_updates``` intermediate frequencies).

The function will return the list on intermediate frequencies at which the correction matrix will be updated in the
program and the four coefficients of the correction matrix with one element for each pair (LO, IF).

### Usage example

```python
from qualang_tools.octave_tools import update_correction_for_each_IF

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
IFs, c00, c01, c10, c11 = update_correction_for_each_IF(
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
    c00_qua = declare(fixed, value=c00)  # QUA variable for the measured 'I' quadrature
    c01_qua = declare(fixed, value=c01)  # QUA variable for the measured 'I' quadrature
    c10_qua = declare(fixed, value=c10)  # QUA variable for the measured 'I' quadrature
    c11_qua = declare(fixed, value=c11)  # QUA variable for the measured 'I' quadrature
    ...
    with for_(i, 0, i < len(lo_frequencies) + 1, i + 1):
        pause()  # This waits until it is resumed from python
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
    qm.octave.set_rf_output_gain("qubit", 0)
    # Update the correction parameters
    set_correction_parameters(
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

## calibrate_several_frequencies
Calibrate a given element for a set of LO and intermediate frequencies. 
Each set of correction parameters will be saved in the calibration database.

### Usage example

```python
from qualang_tools.octave_tools import calibrate_several_frequencies

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
calibrate_several_frequencies(
    qm,
    element="qubit",
    lo_frequencies=lo_frequencies,
    intermediate_frequencies=intermediate_frequencies
)
```