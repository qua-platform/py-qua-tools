# Waveform Tools

## Introduction
---------------
This package includes tools for creating waveforms. 

## Functions
------------
* `drag_gaussian_pulse_waveforms` - Creates Gaussian based DRAG waveforms that compensate for the leakage and for the AC stark shift.
* `drag_cosine_pulse_waveforms` - Creates Cosine based DRAG waveforms that compensate for the leakage and for the AC stark shift.

## Example use case
Example of parameters and how the waveforms can be defined:

```python
from qualang_tools.config.waveform_tools import *
drag_len = 16  # length of pulse in ns
drag_amp = 0.1  # amplitude of pulse in Volts
drag_del_f = 0e6  # Detuning frequency in Hz
drag_alpha = 1  # DRAG coefficient
drag_delta = -200e6 * 2 * np.pi  # in Hz

# Gaussian envelope:
drag_gauss_I_wf, drag_gauss_Q_wf = drag_gaussian_pulse_waveforms(drag_amp, drag_len, drag_len / 5, drag_alpha, drag_delta, drag_del_f, subtracted=False)  # pi pulse

# Cosine envelope:
drag_cos_I_wf, drag_cos_Q_wf = drag_cosine_pulse_waveforms(drag_amp, drag_len, drag_alpha, drag_delta, drag_del_f)  # pi pulse
```
