# Digital filter tools
This library includes tools for deriving the taps of the OPX digital filters (IIR and FIR).

Such filters are generally used to correct for the high-pass filtering occurring on the fast line of a bias-tee, 
or to correct flux pulses for possible distortions happening on the flux lines of superconducting qubit chips.

More details about these types of filter and how they are implemented on the OPX can be found [here](https://docs.quantum-machines.co/1.1.7/qm-qua-sdk/docs/Guides/output_filter/?h=iir#output-filter)

The goal of the following functions is to allow users to easily implement such filters by deriving the IIR and FIR taps 
from the measured distortions. 

## calc_filter_taps
Calculate the best FIR and IIR filter taps for a system with any combination of FIR corrections, exponential
corrections (LPF), high pass compensation, reflections (bounce corrections) and a needed delay on the line.

### Usage examples

#### 
```python
from qualang_tools.loops import from_array

```

## exponential_correction
some explanation

### Usage examples

#### 
```python
from qualang_tools.loops import from_array

```

## highpass_correction
some explanation

### Usage examples

#### 
```python
from qualang_tools.loops import from_array

```

## bounce_and_delay_correction

some explanation

### Usage examples

#### 
```python
from qualang_tools.loops import from_array

```