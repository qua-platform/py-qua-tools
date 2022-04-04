# VNA mode

## Introduction

This module allows to configure the OPX as a VNA for a given element (readout resonator for instance) and 
operation (readout pulse for instance) already defined in the configuration. Once created, it has an API for 
defining which measurements are to be run depending on the down-conversion solution used (ED: envelope detector, 
IR: image rejection mixer, IQ: IQ mixer).

## Usage Example

### Initializing the VNA and set up a S-parameter measurement
This opens up a VNA using an existing configuration and initializes it for the element _element_ and operation _operation_. 
If the element is a resonator, then its quality factor _Q_ can be specified for estimating its relaxation time.
VNA measurements can then be added using the _add_ED()_ (envelope detector), _add_IR()_ (image rejection mixer) and 
_add_IQ()_
(IQ mixer) methods depending on the down-conversion device used.
The results are stored into the dictionary _vna_mode.results_ where the keys are the measurements ('S11' and 'S21' here).
These data can then be plotted using the _plot_all()_ method.

```python
from qualang_tools.control_panel import VNA

# This initializes the VNA for the element 'res' and operation 'readout'
vna_mode = VNA(config, element="res", op="readout", Q=10000)
# This adds S11 and S12 measurements using IR mixers
vna_mode.add_IR_mixer(measurement="S11", outputs="out1", int_weights=["Wc", "Ws"])
vna_mode.add_IR_mixer(measurement="S21", outputs="out2", int_weights=["Wc", "Ws"])
# This runs the two measurements simultaneously with averaging over a 1000 iterations 
freq_sweep = {
  "f_min": 10e6,
  "f_max": 150e6,
  "step": 0.01e6,
}
vna_mode.run_all(freq_sweep, n_avg=1000, dual=True)
# This plots the results stored in vna_mode.results['S11'] and vna_mode.results['S21']
vna_mode.plot_all()
```

### Setup the spectrum analyzer mode
The program below opens up a VNA using an existing configuration and initializes it for the element _element_ and 
operation _operation_.
A spectrum analyzer measurement is added, which will display the temporal trace and fft of the measured signal.
The results (frequency, raw and fft data) are stored into the dictionary _vna_mode.results['SA']_.

```python
from qualang_tools.control_panel import VNA
# This initializes the VNA for the element 'res' and operation 'readout'
vna_mode = VNA(config, element="res", op="fake_readout")
# This adds a spectrum analyzer measurements
vna_mode.add_spectrum_analyzer(bandwidth=1e5)
# This runs the two measurements simultaneously with averaging over a 100 iterations 
vna_mode.run_all(n_avg=100)
vna_mode.plot_all()
```

## List of functions
* ```vna_mode = VNA(config, element, operation, Q=None)``` - Gets a QUA configuration, a corresponding element and an associated 
operation and creates one quantum machine behaving like a VNA.
  * config - A python dictionary containing the QUA configuration.
  * element - element, defined in the configuration, used for subsequent measurements ('readout_res' for example).
  * operation - Operation, defined in the configuration and associated to the element, used to perform subsequent 
  measurements ('readout_pulse' for example). 
  * Q - Quality factor of the resonator under study used to estimate its relaxation time.
* ```add_spectrum_analyzer(bandwidth)``` - Adds a spectrum analyzer measurement to the vna_mode, that will acquire
raw signals outputted by the element and derive its FFT. The corresponding results are stored in the dictionary
my_vna.results['SA'] with the following keys: 'f' for the frequency in Hz, 'raw' for the raw ADC data in V and 'fft' for
the corresponding FFT in V.
  * bandwidth - Measurement bandwidth defining the measurement pulse duration as pulse_length = 2/bandwidth 
  (1e5 for 100kHz for example).
* ```add_envelope_detector(measurement, outputs, int_weights)``` - Adds a S-parameter measurement to the vna_mode in the case where an
down-conversion is made with an envelope detector. The corresponding results are stored in the dictionary
my_vna.results[measurement] with the following keys: 'f' for the frequency in Hz, 'S' for the S magnitude in V and 
'phase' for the S phase in rad.
  * measurement - Measurement type, can be either 'S11' or 'S21'.
  * outputs - Name of the element output port, as defined in the configuration, used for this measurement 
  ('out1' for example).
  * int_weights - Integration weights for the corresponding operation, as defined in the configuration ('Wc' for example).
* ```add_IR_mixer(measurement, outputs, int_weights)``` - Adds an S-parameter measurement to the vna_mode in the case where an
down-conversion is made with an image rejection mixer. The corresponding results are stored in the dictionary
my_vna.results[measurement] with the following keys: 'f' for the frequency in Hz, 'S' for the S magnitude in V and 
'phase' for the S phase in rad.
  * measurement - Measurement type, can be either 'S11' or 'S21'.
  * outputs - Name of the element output port, as defined in the configuration, used for this measurement 
  ('out1' for example).
  * int_weights - list of integration weights for the corresponding operation, as defined in the configuration 
  (['Wc','Ws'] for example).
* ```add_IQ_mixer(measurement, outputs, int_weights)``` - Adds a S-parameter measurement to the vna_mode in the case where an
down-conversion is made with an IQ mixer. The corresponding results are stored in the dictionary
my_vna.results[measurement] with the following keys: 'f' for the frequency in Hz, 'S' for the S magnitude in V and 
'phase' for the S phase in rad.
  * measurement - Measurement type, can be either 'S11' or 'S21'.
  * outputs - List of the element output ports, as defined in the configuration, used for this measurement 
  (["out1", "out2"] for example).
  * int_weights - 2D list of integration weights for the corresponding operation, as defined in the configuration 
  ([["Wc", "Ws"], ["-Ws", "Wc"]] for example).
* ```run_all(freq_sweep=None, n_avg=1, dual=False)``` - Runs all the measurement previously added to the vna mode.
  * freq_sweep - Dictionary containing the frequency sweep parameters used for S-measurements with the following keys: 
  'f_min', 'f_max' and 'step' in Hz 
  (freq_sweep = {"f_min": 10e6, "f_max": 150e6, "step": 0.01e6} for example).
  * n_avg - Number of averaging iterations (n_avg = 1000 for example).
  * dual - Boolean flag controlling the parallelism of the measurements. If two measurements were added, then dual=True
  will run them simultaneously, whereas if dual=False the measurements will be run sequentially.
* ```plot_all()``` - Plots the results of all the performed measurements.
