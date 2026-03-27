"""Tools to help handling QUA loops.

Content:
    - from_array: Function parametrizing the QUA `for_` loop from a python array.
    - qua_arange: Function parametrizing the QUA `for_` loop from the numpy.arange() syntax.
    - qua_linspace: Function parametrizing the QUA `for_` loop from the numpy.linspace() syntax.
    - qua_logspace: Function parametrizing the QUA `for_` loop from the numpy.logspace() syntax.
    - split_frequency_sweep: Function used to split a wide frequency sweep into chunks of a given IF bandwidth and LO steps.
"""

import numpy as np
import warnings
from qm.qua import Cast
from qm.qua import Variable


def from_array(var, array):
    """Function parametrizing the QUA `for_` loop from a python array.

    :param var: the QUA variable that will be looped over (int or fixed).
    :param array: a Python list or numpy array containing the values over which `a` will be looping. The spacing must be even in linear or logarithmic scales and it cannot be a QUA array.
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua.for_.
    """

    # Check for array length
    if len(array) == 0:
        raise Exception("The array must be of length > 0.")
    elif len(array) == 1:
        return var, array[0], var <= array[0], var + 1
    # Check QUA vs python variables
    if not isinstance(var, Variable):
        raise Exception("The first argument must be a QUA variable.")
    if (not isinstance(array[0], (np.generic, int, float))) or (isinstance(array[0], bool)):
        raise Exception("The array must be an array of python variables.")
    # Check array increment
    if np.isclose(np.std(np.diff(array)), 0):
        increment = "lin"
    elif np.isclose(np.std(array[1:] / array[:-1]), 0, atol=1e-3):
        increment = "log"
    else:
        raise Exception(
            "The spacing of the input array must be even in linear or logarithmic scales. Please use `for_each_()` for arbitrary scans."
        )

    # Get the type of the specified QUA variable
    start = array[0]
    stop = array[-1]
    # Linear increment
    if increment == "lin":
        step = array[1] - array[0]

        if var.is_int():
            # Check that the array is an array of int with integer increments
            if not float(step).is_integer() or not float(start).is_integer() or not float(stop).is_integer():
                raise Exception("When looping over a QUA int variable, the step and array elements must be integers.")
            # Generate the loop parameters for positive and negative steps
            if step > 0:
                return var, int(start), var <= int(stop), var + int(step)
            else:
                return var, int(start), var >= int(stop), var + int(step)

        elif var.is_fixed():
            # Check for fixed number overflows
            if not (-8 <= start < 8) and not (-8 <= stop < 8):
                raise Exception("fixed numbers are bounded to [-8, 8).")

            # Generate the loop parameters for positive and negative steps
            if step > 0:
                return (
                    var,
                    float(start),
                    var < float(stop) + float(step) / 2,
                    var + float(step),
                )
            else:
                return (
                    var,
                    float(start),
                    var > float(stop) + float(step) / 2,
                    var + float(step),
                )
        else:
            raise Exception(
                "This variable type is not supported. Please use a QUA 'int' or 'fixed' or contact a QM member for assistance."
            )
    # Logarithmic increment
    elif increment == "log":
        step = array[1] / array[0]

        if var.is_int():
            warnings.warn(
                "When using logarithmic increments with QUA integers, the resulting values will slightly differ from the ones in numpy.logspace() because of rounding errors. \n Please use the get_equivalent_log_array() function to get the exact values taken by the QUA variable and note that the number of points may also change."
            )
            if step > 1:
                if int(round(start) * float(step)) == int(round(start)):
                    raise ValueError(
                        "Two successive values in the scan are equal after being cast to integers which will make the QUA for_ loop fail. \nEither increase the logarithmic step or use for_each_(): https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/features/?h=for_ea#for_each."
                    )
                else:
                    return (
                        var,
                        round(start),
                        var < round(stop) * np.sqrt(float(step)),
                        Cast.mul_int_by_fixed(var, float(step)),
                    )
            else:
                return (
                    var,
                    round(start),
                    var > round(stop) / np.sqrt(float(step)),
                    Cast.mul_int_by_fixed(var, float(step)),
                )

        elif var.is_fixed():
            # Check for fixed number overflows
            if not (-8 <= start < 8) and not (-8 <= stop < 8):
                raise Exception("fixed numbers are bounded to [-8, 8).")

            if step > 1:
                return (
                    var,
                    float(start),
                    var < float(stop) * np.sqrt(float(step)),
                    var * float(step),
                )
            else:
                return (
                    var,
                    float(start),
                    var > float(stop) * np.sqrt(float(step)),
                    var * float(step),
                )
        else:
            raise Exception(
                "This variable type is not supported. Please use a QUA 'int' or 'fixed' or contact a QM member for assistance."
            )


def qua_arange(var, start, stop, step):
    """Function parametrizing the QUA `for_` loop from the numpy.arange() syntax.

    :param var: the QUA variable that will be looped over (int or fixed).
    :param start: Start of interval. The interval includes this value. Must be a Python variable.
    :param stop: End of interval. The interval does not include this value. Must be a Python variable.
    :param step: Spacing between values. Must be a Python variable.
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua.for_.
    """
    # Check QUA vs python variables
    if not isinstance(var, Variable):
        raise Exception("The first argument must be a QUA variable.")
    if (
        (not isinstance(start, (np.generic, int, float)))
        or (not isinstance(stop, (np.generic, int, float)))
        or (not isinstance(step, (np.generic, int, float)))
        or (isinstance(start, bool))
        or (isinstance(stop, bool))
        or (isinstance(step, bool))
    ):
        raise Exception("The for loop arguments must be python variables.")
    if float(step).is_integer():
        stop_condition = stop
    else:
        # Check for fixed number overflows
        if not (-8 <= start < 8) and not (-8 <= stop < 8):
            raise Exception("fixed numbers are bounded to [-8, 8).")
        if ((stop - start) / step).is_integer():
            stop_condition = stop - step / 2
        else:
            stop_condition = stop

        if np.abs((stop - start) / step * 2**-28) >= np.abs(step):
            raise Exception("The required accuracy is to large:N * (2 ** -28) > step/2, please contact a QM member.")

    if step > 0:
        return var, start, var < stop_condition, var + step
    else:
        return var, start, var > stop_condition, var + step


def qua_linspace(var, start, stop, num):
    """Function parametrizing the QUA `for_` loop from the numpy.linspace() syntax.

    :param var: the QUA variable that will be looped over (int or fixed).
    :param start: The starting value of the sequence. The interval includes this value. Must be a Python variable.
    :param stop: The end value of the sequence. The interval includes this value within the 2**-28 fixed point accuracy. Must be a Python variable.
    :param num: Number of samples to generate. Must be a Python variable.
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua.for_.
    """
    # Check QUA vs python variables
    if not isinstance(var, Variable):
        raise Exception("The first argument must be a QUA variable.")
    if (
        (not isinstance(start, (np.generic, int, float)))
        or (not isinstance(stop, (np.generic, int, float)))
        or (not isinstance(num, (np.generic, int, float)))
        or (isinstance(start, bool))
        or (isinstance(stop, bool))
        or (isinstance(num, bool))
    ):
        raise Exception("The for loop arguments must be python variables.")
    # Check for fixed number overflows
    if not (-8 <= start < 8) and not (-8 <= stop < 8):
        raise Exception("fixed numbers are bounded to [-8, 8).")
    # Check if num is integer
    if not float(num).is_integer():
        raise Exception("The number of samples must be a python integer.")

    if num > 1:
        step = (stop - start) / (num - 1)
    elif num == 1:
        step = (stop - start) * 2
    else:
        step = stop - start

    if step > 0:
        return var, start, var < stop + step / 2, var + step
    else:
        return var, start, var > stop + step / 2, var + step


def qua_logspace(var, start, stop, num):
    """Function parametrizing the QUA `for_` loop from the numpy.logspace() syntax.

    :param var: the QUA variable that will be looped over (fixed).
    :param start: The starting value of the sequence as 10**start in linear space. The interval includes this value. Must be a Python variable.
    :param stop: The end value of the sequence as 10**stop in linear space. The interval includes this value within the 2**-28 fixed point accuracy. Must be a Python variable.
    :param num: Number of samples to generate. Must be a Python variable.
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua.for_.
    """
    # Check QUA vs python variables
    if not isinstance(var, Variable):
        raise Exception("The first argument must be a QUA variable.")
    if (
        (not isinstance(start, (np.generic, int, float)))
        or (not isinstance(stop, (np.generic, int, float)))
        or (not isinstance(num, (np.generic, int, float)))
        or (isinstance(start, bool))
        or (isinstance(stop, bool))
        or (isinstance(num, bool))
    ):
        raise Exception("The for loop arguments must be python variables.")
    # Check if num is integer
    if not float(num).is_integer():
        raise Exception("The number of samples must be a python integer.")

    if num > 1:
        step = (10**stop / 10**start) ** (1 / (num - 1))
    elif num == 1:
        step = (10**stop / 10**start) ** 1
    else:
        raise Exception("`num` must be greater than 0.")

    # Get the type of the specified QUA variable
    if var.is_int():
        warnings.warn(
            "When using logarithmic increments with QUA integers, the resulting values will slightly differ from the ones in numpy.logspace() because of rounding errors. \n Please use the get_equivalent_log_array() function to get the exact values taken by the QUA variable and note that the number of points may also change."
        )
        if step > 1:
            if int(round(10**start) * float(step)) == int(round(10**start)):
                raise ValueError(
                    "Two successive values in the scan are equal after being cast to integers which will make the QUA for_ loop fail. \nEither increase the logarithmic step or use for_each_(): https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/features/?h=for_ea#for_each."
                )
            else:
                return (
                    var,
                    round(10**start),
                    var < round(10**stop * np.sqrt(step)),
                    Cast.mul_int_by_fixed(var, float(step)),
                )
        else:
            return (
                var,
                round(10**start),
                var > round(10**stop / np.sqrt(step)),
                Cast.mul_int_by_fixed(var, float(step)),
            )
    elif var.is_fixed():
        # Check for fixed number overflows
        if not (-8 <= 10**start < 8) and not (-8 <= 10**stop < 8):
            raise Exception("fixed numbers are bounded to [-8, 8).")

        if step > 1:
            return (
                var,
                10**start,
                (var < 10**stop * np.sqrt(step)) & (10**start <= var),
                var * step,
            )
        else:
            return (
                var,
                10**start,
                (var > 10**stop * np.sqrt(step)) & (10**start >= var),
                var * step,
            )


def get_equivalent_log_array(log_array):
    """Function returning the values taken by the QUA int variable within the logarithmic QUA `for_` loop.
    Because of rounding errors occuring with QUA integers, these values are not exactly the ones given by `numpy.logspace()`.
    Note that the number of points may also change.

    :param log_array: a Python list or numpy array containing the values parametrizing the QUA `for_` loop. The spacing must be even in logarithmic scale and it cannot be a QUA array.
    :return: numpy array containing the values taken by the QUA int variable within the logarithmic QUA `for_` loop.
    """
    a_log = []
    aprev = round(log_array[0])
    step = np.mean(np.array(log_array[1:]) / np.array(log_array[:-1]))

    if step > 1:
        end = log_array[-1] * np.sqrt(step)
        while aprev < end:
            a_log.append(aprev)
            if aprev == int(aprev * step):
                raise ValueError(
                    "Two successive values in the scan are equal after being cast to integers which will make the QUA for_ loop fail. \nEither increase the logarithmic step or use for_each_() instead of from_array(): https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/features/?h=for_ea#for_each."
                )
            else:
                aprev = int(aprev * step)
    else:
        end = log_array[-1] / np.sqrt(step)
        while aprev > end:
            a_log.append(aprev)
            if aprev == int(aprev * step):
                raise ValueError(
                    "Two successive values in the scan are equal after being cast to integers which will make the QUA for_ loop fail. \nEither increase the logarithmic step or use for_each_() instead of from_array(): https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/features/?h=for_ea#for_each."
                )
            else:
                aprev = int(aprev * step)
    return np.array(a_log)


def split_frequency_sweep(fmin: float, fmax: float, df: float, max_if_bandwidth: float=800e6, symmetric_span: bool = True,
    if_min_hz: float = 1e6):
    """
    Plan an RF frequency sweep as repeated **LO + IF** steps.

    The mixer relation is ``f_rf = f_lo + f_if``. For each LO ``f_lo[j]``, the
    same IF template ``f_if[k]`` is used so every RF tone lies on
    ``fmin + i * df``. The RF grid may be **extended** past ``fmax`` so its
    length is a multiple of the IF length (one template, fewest LO steps).

    **Symmetric IF (``symmetric_span=True``, default)**
    IF is centered around 0 in the sense that ``f_lo[j]`` is the **midpoint**
    of segment ``j`` on the RF grid, and ``f_if`` runs from about
    ``-(n_if-1)*df/2`` to ``+(n_if-1)*df/2``. The usable IF span per LO obeys
    ``(n_if - 1) * df <= max_if_bandwidth`` (same as a symmetric window of
    width ``max_if_bandwidth`` around the LO).

    **Asymmetric IF (``symmetric_span=False``)**
    IF is one-sided: ``f_if[k] = if_min_hz + k * df`` with
    ``if_min_hz <= f_if <= max_if_bandwidth`` for the last point, i.e.
    ``(n_if - 1) * df <= max_if_bandwidth - if_min_hz``. Here
    ``f_lo[j] = rf_segment_start[j] - if_min_hz`` (not the segment midpoint).

    Parameters
    ----------
    fmin, fmax : float
        RF sweep range in Hz; ``fmax >= fmin``.
    df : float
        RF step in Hz; must be positive.
    max_if_bandwidth : float
        Maximum span in Hz of the IF sweep for one LO: ``(n_if - 1) * df`` with
        ``(n_if - 1) * df <= max_if_bandwidth`` (same as max RF span of one
        segment, since IF and RF share the same step ``df`` on this grid).
        Default is 800MHz.
    symmetric_span : bool, default True
        If True, IF is symmetric about 0 (LO at segment midpoint). If False,
        IF lies in ``[if_min_hz, max_if_bandwidth]`` to account for possible high-pass limitations of the hardware.
    if_min_hz : float, default 1e6
        Lower edge of IF when ``symmetric_span`` is False; ignored when True.

    Returns
    -------
    los : list of float
        Local oscillator frequency for each segment (midpoint of that segment's
        RF grid).
    if_offsets : list of float
        Intermediate-frequency offsets for one LO step, relative to ``los[0]``,
        such that ``f_rf[j, k] = los[j] + if_offsets[k]`` matches the full RF
        grid (including extension). Same length as the number of IF points per
        LO.
    rf_freqs : ndarray
        Full RF grid ``fmin + arange(n) * df`` (extended if needed).
    """
    if fmax < fmin:
        raise ValueError("fmax must be >= fmin")
    if df <= 0:
        raise ValueError("df must be positive")
    if max_if_bandwidth <= 0:
        raise ValueError("max_if_bandwidth must be positive")
    if not symmetric_span:
        if if_min_hz < 0:
            raise ValueError("if_min_hz must be non-negative")
        if max_if_bandwidth <= if_min_hz:
            raise ValueError(
                "max_if_bandwidth must be greater than if_min_hz when symmetric_span is False"
            )

    n_rf_original = int(np.floor((fmax - fmin) / df + 1e-12)) + 1
    if n_rf_original <= 0:
        return [], [], np.array([], dtype=np.float64), 0
    if n_rf_original == 1:
        f0 = np.array([fmin], dtype=np.float64)
        return [float(fmin)], [0.0], f0, 1

    if symmetric_span:
        max_if_span_hz = max_if_bandwidth
    else:
        max_if_span_hz = max_if_bandwidth - if_min_hz

    n_if_max = int(np.floor(max_if_span_hz / df + 1e-12)) + 1
    n_if_max = max(1, n_if_max)
    n_if_points = n_if_max
    n_rf_total = n_if_points * int(np.ceil(n_rf_original / n_if_points))

    rf_freqs = fmin + np.arange(n_rf_total, dtype=np.float64) * df
    n_lo_steps = n_rf_total // n_if_points
    rf_segments = [rf_freqs[j * n_if_points: (j + 1) * n_if_points] for j in range(n_lo_steps)]

    if symmetric_span:
        los = [float((float(seg[0]) + float(seg[-1])) / 2.0) for seg in rf_segments]
        lo0 = los[0]
        if_offsets = [float(f_rf - lo0) for f_rf in rf_segments[0]]
    else:
        los = [float(seg[0]) - if_min_hz for seg in rf_segments]
        if_offsets = [float(if_min_hz + k * df) for k in range(n_if_points)]

    return los, if_offsets, rf_freqs
