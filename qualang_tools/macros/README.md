# Macros
This module includes convenience functions for encapsulating commonly-used QUA macros.

## long_wait
As opposed to the `wait` command which suffers from a maximum wait time and long compilation times for large
waiting constants, `long_wait` simply loops many shorter `wait` commands to achieve arbitrarily long waiting times.

### Example
```python
from qm.qua import program
from qualang_tools.macros import long_wait
from qualang_tools.units import unit

u = unit()
with program() as prog:
    play(...)
    # wait on all elements for 30 seconds
    long_wait(30 * u.s)
    # wait on a elements `qe1` and `qe2` for 20s
    long_wait(20 * u.s, "qe1", "qe2")
    # wait on all elements for a short time, defaulting to usual `wait` behaviour
    long_wait(100 * u.us)
    # wait on all elements, compile to multiple 500us waits if wait time is longer than 500us
    long_wait(2 * u.ms, threshold_for_looping=500*u.us)
    measure(...)
```