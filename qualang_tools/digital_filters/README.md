# Digital filter tools
This library includes tools for deriving the taps of the OPX digital filters (IIR and FIR).

Such filters are generally used to correct for the high-pass filtering occurring on the fast line of a bias-tee, 
or to correct flux pulses for possible distortions happening on the flux lines of superconducting qubit chips.

More details about these types of filter and how they are implemented on the OPX can be found [here](https://docs.quantum-machines.co/1.1.7/qm-qua-sdk/docs/Guides/output_filter/?h=iir#output-filter)

The goal of the following functions is to allow users to easily implement such filters by deriving the IIR and FIR taps 
from the measured distortions:
* [Exponential decay](#exponentialcorrection): fit a low-pass exponential decay `1 + A * exp(-t/tau)`.
* [Exponential correction](#exponentialcorrection): correct for a low-pass exponential decay `1 + A * exp(-t/tau)`.
* [Highpass correction](#highpasscorrection): correct for a high pass exponential decay `exp(-t/tau)`.
* [Bounce and delay correction](#bounceanddelaycorrection): correct for reflections and delays.
* [Calc filter taps](#calcfiltertaps): correct for any combination of the aforementioned compensations.

## Usage examples

### exponential_correction
Calculate the best FIR and IIR filter taps to correct for an exponential decay (low-pass filter) of the shape
`exponential_decay(t, A, tau) = 1 + A * exp(-t/tau)`.

#### 
```python
from scipy import optimize
from qualang_tools.digital_filters import exponential_decay, exponential_correction

# Fit your data with the exponential_decay function
[A, tau_ns], _ = optimize.curve_fit(
        exponential_decay,
        time_axis_in_ns,
        data_to_fit,
    )
# Derive the corresponding taps
feedforward_taps, feedback_tap = exponential_correction(A, tau_ns)
# Update the config with the digital filter parameters
config["controllers"]["con1"]["analog_outputs"][port_number] = {
    "offset": 0.0, 
    "filter": {"feedforward": feedforward_taps, "feedback": feedback_tap}}
```

### highpass_correction
Calculate the best FIR and IIR filter taps to correct for a highpass decay (high-pass filter) of the shape `exp(-t/tau)`.

#### 
```python
from qualang_tools.digital_filters import highpass_correction

# Derive the taps from the time constant of the exponential highpass decay tau
feedforward_taps, feedback_tap = highpass_correction(tau_ns)
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
corrections (LPF), high pass compensation, reflections (bounce corrections) and a needed delay on the line.

#### 
```python
from scipy import optimize
from qualang_tools.digital_filters import exponential_decay
from qualang_tools.digital_filters import calc_filter_taps


# Fit your data with the exponential_decay function
[A, tau_ns], _ = optimize.curve_fit(
        exponential_decay,
        time_axis_in_ns,
        data_to_fit,
    )
# Derive the taps for correction all the identified distortions (high-pass, low-pass, reflection and delay) 
feedforward_taps, feedback_tap = calc_filter_taps(
    fir=None,
    exponential=[(A, tau_ns),],
    highpass=[tau_hpf],
    bounce=[(a_bounce, tau_bounce),],
    delay=,
)
# Update the config with the digital filter parameters
config["controllers"]["con1"]["analog_outputs"][port_number] = {
    "offset": 0.0, 
    "filter": {"feedforward": feedforward_taps, "feedback": feedback_tap}}
```
