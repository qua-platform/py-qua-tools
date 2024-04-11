from typing import Union

import numpy as np
from qm.qua import declare, wait, for_
from qualang_tools.addons.calibration.calibrations import u

MAX_WAIT = 2**31 - 1  # units of clock cycles (4ns)


def long_wait(wait_time: Union[int, np.integer], *elements: str, threshold_for_looping: int = u.to_clock_cycles(1e6)):
    """Perform a QUA wait command for longer than the current maximum wait time, 2^31-1.

    This macro unrolls into QUA for-loop of smaller waits if the maximum wait time is exceeded in `wait_time`.

    Note: `wait_time` must be a python integer, not a QUA variable.

    Args:
        wait_time (int): Desired wait time in units of clock cycles (4ns).
        *elements (str): Variable length argument list of elements to wait on.
        threshold_for_looping: Minimum wait time at which `long_wait` uses a QUA for-loop of waits (default 1ms).
         1ms is chosen as a safe default because constants larger than 1e6 in a QUA program tend to extend compilation
         times. In units of clock cycles.
    """
    if not isinstance(wait_time, (int, np.integer)):
        raise TypeError(f"Expected wait_time to be a float or an integer, got {type(wait_time)}.")

    if threshold_for_looping < 4:
        raise ValueError(f"Expected loop threshold to be greater than 4 clock cycles, got {threshold_for_looping}")

    if threshold_for_looping > MAX_WAIT:
        raise ValueError(
            f"Expected loop threshold to be less than the maximum wait time {MAX_WAIT}, got {threshold_for_looping}"
        )

    if wait_time < threshold_for_looping:
        wait(wait_time, *elements)

    else:
        # this QUA variable name shouldn't interfere with commonly used QUA variable names, e.g. i = declare(int)
        _long_wait_loop_index = declare(int)

        loop_runs = (wait_time // threshold_for_looping) - 1

        # wait for N x threshold wait time
        with for_(_long_wait_loop_index, 0, _long_wait_loop_index < loop_runs, _long_wait_loop_index + 1):
            wait(threshold_for_looping, *elements)

        # wait for the remainder
        wait(int(wait_time - threshold_for_looping * loop_runs), *elements)
