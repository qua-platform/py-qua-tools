# Units tools
This library includes tools to help handling units and conversions.

## Unit
This class has an API for introducing units and conversion methods.

The available units are regrouped in the table below:

| Unit   | ns  | us   | ms   | s    | mHz   | Hz  | kHz | MHz  | GHz  | uV    | mV  | V   |
|--------|-----|------|------|------|-------|-----|-----|------|------|-------|-----|-----|
| factor | 1   | 10^3 | 10^6 | 10^9 | 10^-3 | 1   | 10^3| 10^6 | 10^9 | 10^-6 | 10^-3 | 1   |

Please note the [special behavior of time units](#time-units)

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

### Time Units

Time units are specified differently while declaring a python variable or in the context of a qua `program`. 
In particular, in python, time is defined in **nanoseconds**, while in a qua program it must be specified in units of **clock cycles of the FPGA** (of the duration of 4 nanoseconds).
`unit` respects this behavior, and the value of time units is calculated dynamically depending on the context.
This translates to the normal behavior of time units being

```python
u.ns == 1 # Times are in ns in python
```

while inside a qua `program`

```python
with program() as prog:
    4 * u.ns == 1 # Times are in clock cycles in qua
```

#### Usage Example

```python
from qm.qua import *
from qualang_tools.units import unit

u = unit()

pulse_duration_in_ns = 40 * u.ns # == 40

with program() as prog:
    play('pulse1', 'element1', duration = pulse_duration_in_ns * u.ns)
    # Automatically converts the duration to 10 clock cycles
```

#### Casting and Warnings

The OPX only supports an **integer number** of clock cycles. Therefore, the result of a multiplication with `u.ns` and similar time units **can be automatically cast to `int`**.
For example

```python
with program() as prog:
    6 * u.ns == 1
```

This behavior is **disabled** by default and can be enabled when declaring `unit` as

```python
u = unit(coerce_to_integer = True)
```

If casting occurs with nonzero reminder, (e.g. `6 * u.ns`), this will emit a `RuntimeWarning`. This can be avoided by declaring

```python
u = unit(verbose = False)
```

### Frequency Units

To avoid floating point errors and incompatibilities with some configuration entries and mixer calibration parameters, 
the flag ``coerce_to_integer = True`` will automatically round and cast to integers the frequencies defined with the 
unit class. 
For instance:

```python
u = unit(coerce_to_integer = True)

qubit_LO = 4.1 * u.GHz # --> will return 4_100_000_000 instead of 4099999999.9999995 (= 4.1 * 1e9)
qubit_IF = 4.1 * u.MHz # --> Will return 4_100_000 instead of 4099999.9999995 (= 4.1 * 1e6)
```
