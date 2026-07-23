"""Tools to help handling QUA loops.

Content:
    - from_array: Function parametrizing the QUA `for_` loop from a python array.
    - qua_arange: Function parametrizing the QUA `for_` loop from the numpy.arange() syntax.
    - qua_linspace: Function parametrizing the QUA `for_` loop from the numpy.linspace() syntax.
    - qua_logspace: Function parametrizing the QUA `for_` loop from the numpy.logspace() syntax.
"""

import numpy as np
import warnings
from qm.qua import Cast
from qm.qua import Variable


def _fixed_literal_step_ok(step):
    return abs(float(step)) <= 8


def _raise_fixed_literal_step(step):
    raise ValueError(
        "For QUA fixed variables, the increment or logarithmic ratio used in the loop update must satisfy |step| <= 8; "
        "larger values are not representable and can overflow. " + "Use for_each_() for arbitrary scans: "
        "https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/features/?h=for_ea#for_each."
    )


def _raise_fixed_points():
    raise ValueError(
        "For QUA fixed variables, every value visited in the loop must lie in [-8, 8). "
        + "Use for_each_() for arbitrary scans: "
        "https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/features/?h=for_ea#for_each."
    )


def _raise_fixed_post_update():
    raise ValueError(
        "For QUA fixed variables, the value after the loop update (var + step or var * step) must remain in [-8, 8); "
        "otherwise the hardware update overflows or wraps before the next condition check. "
        "Use for_each_() for arbitrary scans: "
        "https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/features/?h=for_ea#for_each."
    )


def _in_fixed_range(x):
    return -8 <= float(x) < 8


def _validate_fixed_array_points(array):
    pts = np.asarray(array, dtype=float)
    if not np.all((pts >= -8) & (pts < 8)):
        _raise_fixed_points()


def _simulate_from_array_fixed_linear(start, stop, step):
    fs, fst, fstp = float(start), float(stop), float(step)
    visited = []
    if fstp > 0:
        v = fs
        thresh = fst + fstp / 2
        while v < thresh:
            visited.append(v)
            v += fstp
            if not _in_fixed_range(v):
                _raise_fixed_post_update()
    else:
        v = fs
        thresh = fst + fstp / 2
        while v > thresh:
            visited.append(v)
            v += fstp
            if not _in_fixed_range(v):
                _raise_fixed_post_update()
    return visited


def _simulate_from_array_fixed_log(start, stop, step):
    fs, fst, fstp = float(start), float(stop), float(step)
    visited = []
    if fstp > 1:
        v = fs
        thresh = fst * np.sqrt(fstp)
        while v < thresh:
            visited.append(v)
            v *= fstp
            if not _in_fixed_range(v):
                _raise_fixed_post_update()
    else:
        v = fs
        thresh = fst * np.sqrt(fstp)
        while v > thresh:
            visited.append(v)
            v *= fstp
            if not _in_fixed_range(v):
                _raise_fixed_post_update()
    return visited


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
            if not (-8 <= start < 8) or not (-8 <= stop < 8):
                raise Exception("fixed numbers are bounded to [-8, 8).")

            _validate_fixed_array_points(array)
            if not _fixed_literal_step_ok(step):
                _raise_fixed_literal_step(step)

            visited = _simulate_from_array_fixed_linear(start, stop, step)
            for v in visited:
                if not (-8 <= v < 8):
                    _raise_fixed_points()

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
            if not (-8 <= start < 8) or not (-8 <= stop < 8):
                raise Exception("fixed numbers are bounded to [-8, 8).")

            _validate_fixed_array_points(array)
            if not _fixed_literal_step_ok(step):
                _raise_fixed_literal_step(step)

            visited = _simulate_from_array_fixed_log(start, stop, step)
            for v in visited:
                if not (-8 <= v < 8):
                    _raise_fixed_points()

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
        if var.is_fixed():
            if not (-8 <= start < 8) or not (-8 <= stop < 8):
                raise Exception("fixed numbers are bounded to [-8, 8).")
            if not _fixed_literal_step_ok(step):
                _raise_fixed_literal_step(step)
            seq = np.arange(float(start), float(stop), float(step))
            for v in seq:
                if not (-8 <= v < 8):
                    _raise_fixed_points()
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
    if var.is_fixed():
        if not (-8 <= start < 8) or not (-8 <= stop < 8):
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

    if var.is_fixed():
        if not _fixed_literal_step_ok(step):
            _raise_fixed_literal_step(step)
        n = int(num)
        if n > 1:
            seq = np.linspace(float(start), float(stop), n)
        elif n == 1:
            seq = np.array([float(start)])
        else:
            seq = np.array([])
        for v in seq:
            if not (-8 <= v < 8):
                _raise_fixed_points()

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
        if abs(step) >= 8:
            _raise_fixed_literal_step(step)
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
        if not (-8 <= 10**start < 8) or not (-8 <= 10**stop < 8):
            raise Exception("fixed numbers are bounded to [-8, 8).")

        if not _fixed_literal_step_ok(step):
            _raise_fixed_literal_step(step)
        n = int(num)
        if n > 1:
            seq = np.logspace(float(start), float(stop), n, base=10.0)
        elif n == 1:
            seq = np.array([10 ** float(start)])
        else:
            seq = np.array([])
        for v in seq:
            if not (-8 <= v < 8):
                _raise_fixed_points()

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
