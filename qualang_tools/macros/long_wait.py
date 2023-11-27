from typing import Union
from qm.qua import declare, wait, for_

MAX_WAIT = 2**31 - 1  # units of clock cycles (4ns)


def long_wait(wait_time: Union[float, int], *elements: str):
    """Perform a QUA wait command for longer than the current maximum wait time, 2^31-1.

    This macro unrolls into QUA for-loop of smaller waits if the maximum wait time is exceeded in `wait_time`.

    Args:
        wait_time (Union[float, int]): Desired wait time in units of clock cycles (4ns).
        *elements (str): Variable length argument list of elements to wait on.
    """
    i = declare(int)
    if wait_time < MAX_WAIT:
        wait(wait_time, *elements)
    else:
        loop_runs = (wait_time // MAX_WAIT) - 1
        with for_(i, 0, i < loop_runs, i + 1):
            wait(MAX_WAIT, *elements)
        wait(int(wait_time - MAX_WAIT * loop_runs), *elements)
