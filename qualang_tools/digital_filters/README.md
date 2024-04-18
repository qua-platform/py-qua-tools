# Digital filter tools
This library includes tools for deriving the taps of the OPX digital filters (IIR and FIR).

Such filters are generally used to correct for the high-pass filtering occurring on the fast line of a bias-tee, 
or to correct flux pulses for possible distortions happening on the flux lines of superconducting qubit chips.

More details about these types of filter and how they are implemented on the OPX can be found [here](https://docs.quantum-machines.co/1.1.7/qm-qua-sdk/docs/Guides/output_filter/?h=iir#output-filter)

The goal of the following functions is to allow users to easily implement such filters by deriving the IIR and FIR taps 
from the measured distortions:
* [Single exponential correction](#singleexponentialcorrection): correct for a low-pass exponential decay `1 + A * exp(-t/tau)`.
* [Highpass correction](#highpasscorrection): correct for a high pass exponential decay `exp(-t/tau)`.
* [Bounce and delay correction](#bounceanddelaycorrection): correct for reflections and delays.
* [Calc filter taps](#calcfiltertaps): correct for any combination of the aforementioned compensations.

## Usage examples

### single_exponential_correction
Calculate the best FIR and IIR filter taps to correct for an exponential decay (undershoot or overshoot) of the shape
`1 + A * exp(-t/tau)`. You can use the `exponential_decay` function for fitting your data as shown below.

#### 
```python
from scipy import optimize
from qualang_tools.digital_filters import exponential_decay, single_exponential_correction

# Fit your data with the exponential_decay function
[A_lpf, tau_lpf_ns], _ = optimize.curve_fit(
    exponential_decay,
    x_data,
    y_data,
)
# Derive the corresponding taps
feedforward_taps, feedback_tap = single_exponential_correction(A_lpf, tau_lpf_ns)
# Update the config with the digital filter parameters
config["controllers"]["con1"]["analog_outputs"][port_number] = {
    "offset": 0.0, 
    "filter": {"feedforward": feedforward_taps, "feedback": feedback_tap}}
```

### highpass_correction
Calculate the best FIR and IIR filter taps to correct for a highpass decay (high-pass filter) of the shape `exp(-t/tau)`.
You can use the `high_pass_exponential` function for fitting your data as shown below.

#### 
```python
from scipy import optimize
from qualang_tools.digital_filters import high_pass_exponential, highpass_correction

# Fit your data with the exponential_decay function
[tau_hpf_ns], _ = optimize.curve_fit(
    high_pass_exponential,
    x_data,
    y_data,
)
# Derive the taps from the time constant of the exponential highpass decay tau
feedforward_taps, feedback_tap = highpass_correction(tau_hpf_ns)
# Update the config with the digital filter parameters
config["controllers"]["con1"]["analog_outputs"][port_number] = {
    "offset": 0.0, 
    "filter": {"feedforward": feedforward_taps, "feedback": feedback_tap}}
```

### bounce_and_delay_correction
Calculate the FIR filter taps to correct for reflections (bounce corrections) and to add a delay.

#### 
```python
from qualang_tools.digital_filters import bounce_and_delay_correction



```

### calc_filter_taps
Calculate the best FIR and IIR filter taps for a system with any combination of FIR corrections, exponential
corrections (undershoot or overshoot), high pass compensation, reflections (bounce corrections) and a needed delay on the line.

#### 
```python
from qualang_tools.digital_filters import calc_filter_taps

# Derive the taps for correction all the identified distortions (high-pass, low-pass, reflection and delay) 
feedforward_taps, feedback_tap = calc_filter_taps(
    fir=None,
    exponential=list(zip([A_lpf_1, A_lpf_2,...], [tau_lpf_ns_1, tau_lpf_ns_2,...])),
    highpass=[tau_hpf_ns],
    bounce=[(a_bounce, tau_bounce),],
    delay=20,
)
# Update the config with the digital filter parameters
config["controllers"]["con1"]["analog_outputs"][port_number] = {
    "offset": 0.0, 
    "filter": {"feedforward": feedforward_taps, "feedback": feedback_tap}}
```
