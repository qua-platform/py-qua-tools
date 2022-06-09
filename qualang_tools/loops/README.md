# Loops tools
This library includes tools for parametrizing QUA `for_` loop. 

As opposed the `for_each_` method which suffers from large memory usage and may introduce gaps, 
these functions simplify the usage of QUA for loop without any costs in terms of ressources and performance.

## from_array
This function allows to parametrize a QUA `for_` loop using a predefined python array.
Note that this array must have a linear or logarithmic increment. For looping over arbitrary arrays, 
please use the QUA `for_each_` method.

### Usage examples

#### With *numpy.arange()* and a QUA variable of type *fixed*
```python
from qualang_tools.loops import from_array
import numpy as np 

pulse_amplitude = np.arange(-0.3, 0.3 , 0.01)

with program() as prog:
    a = declare(fixed)
    with for_(*from_array(a, pulse_amplitude)):
        # The variable 'a' will be looped over the values from pulse_amplitude
        ...
```

#### With *numpy.logspace()* and a QUA variable of type *int*
When looping a QUA int with a logarithmic increment the values taken by the QUA variable slightly differ from the ones 
in numpy.logspace because of rounding errors. The exact values taken by the QUA variable can be retrieved using the 
`get_equivalent_log_array(log_array)` function as shown below: 
```python
from qualang_tools.loops import from_array, get_equivalent_log_array
import numpy as np 

qubit_frequency = np.logspace(3, 6, 101)
exact_qubit_frequency = get_equivalent_log_array(qubit_frequency)

with program() as prog:
    f = declare(int)
    with for_(*from_array(f, qubit_frequency)):
        # The variable 'f' will be looped over the values from exact_qubit_frequency
        ...
```

Note that this does not happen when looping over a QUA variable of type fixed, or when using a linear increment.

## qua_arange

This function allows to parametrize a QUA `for_` loop using the same formalism as with `numpy.arange(start, stop, step)`.
Note that the 'stop' point will not be included in the loop.

### Usage example

```python
from qualang_tools.loops import qua_arange

a_min = -0.3
a_max = 0.3
da = 0.01

with program() as prog:
    a = declare(fixed)
    with for_(*qua_arange(a, a_min, a_max, da)):
        # The variable 'a' will take the same values as the ones in np.arange(a_min, a_max , da)
        ...
```

## qua_linspace

This function allows to parametrize a QUA `for_` loop using the same formalism as with `numpy.linspace(start, stop, num)`.
Note that the 'stop' value will be included into the loop.

### Usage example

```python
from qualang_tools.loops import qua_linspace

a_min = -0.3
a_max = 0.3
a_len = 101

with program() as prog:
    a = declare(fixed)
    with for_(*qua_linspace(a, a_min, a_max, a_len)):
        # The variable 'a' will take the same values as the ones in np.linspace(a_min, a_max , a_len)
        ...
```

## qua_logspace

This function allows to parametrize a QUA `for_` loop using the same formalism as with `numpy.logspace(start, stop, num)`.
Note that the 'stop' value will be included into the loop.

### Usage examples

#### With a QUA variable of type *fixed*

```python
from qualang_tools.loops import qua_logspace

a_min = -4
a_max = -0.302
a_len = 101

with program() as prog:
    a = declare(fixed)
    with for_(*qua_logspace(a, a_min, a_max, a_len)):
        # The variable 'a' will take the same values as the ones in np.logspace(a_min, a_max , a_len)
        ...
```
Note that the values between a_min and a_max must be included in [-8, 8).

#### With a QUA variable of type *int*
When looping a QUA int with a logarithmic increment the values taken by the QUA variable slightly differ from the ones 
in numpy.logspace because of rounding errors. The exact values taken by the QUA variable can be retrieved using the 
`get_equivalent_log_array(log_array)` function as shown below: 
```python
from qualang_tools.loops import from_array, get_equivalent_log_array
import numpy as np 

f_min = 3
f_max = 6
f_len = 101

exact_qubit_frequency = get_equivalent_log_array(np.logspace(f_min, f_max, f_len))

with program() as prog:
    f = declare(int)
    with for_(*qua_logspace(f, f_min, f_max, f_len)):
        # The variable 'f' will be looped over the values from exact_qubit_frequency
        ...
```