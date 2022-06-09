# Units tools
This library includes tools to help handling units and conversions.

## Unit
This class has an API for introducing units and conversion methods.

The available units are regrouped in the table below:

| Unit   | ns  | us   | ms   | s    | mHz   | Hz  | kHz | MHz  | GHz  | uV    | mV  | V   |
|--------|-----|------|------|------|-------|-----|-----|------|------|-------|-----|-----|
| factor | 1   | 10^3 | 10^6 | 10^9 | 10^-3 | 1   | 10^3| 10^6 | 10^9 | 10^-6 | 10^-3 | 1   |

Several conversion methods are available:
- `to_clock_cycles(t)`: Converts a duration to clock cycles.
- `demod2volts(data, duration)`: Converts the demodulated data to volts.
- `raw2volts(data)`: Converts the raw data to volts.

### Usage example

 
```python
from qualang_tools.units import unit

u = unit()

qubit_LO = 6.8957 * u.GHz
qubit_IF = 245 * u.MHz

readout_len = 256 * u.us
pi_len = 224 * u.ns
qubit_T1 = 6 * u.ms

plt.figure()
plt.scatter(u.demod2volts(I, readout_len) * u.uV, u.demod2volts(Q, readout_len)* u.uV)
plt.xlabel("I quadrature [µV]")
plt.ylabel("Q quadrature [µV]")

plt.figure()
plt.plot(u.raw2volts(raw_data) * u.mV)
plt.ylabel("Raw trace [mV]")
```

