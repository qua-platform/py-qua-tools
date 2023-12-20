# Octave Tools
This library includes tools to improve the users Octave experience.

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

### Usage example

```python

```