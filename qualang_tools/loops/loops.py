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
from qm.qua._dsl import _Expression


def from_array(var, array):
    """Function parametrizing the QUA `for_` loop from a python array.

    :param var: the QUA variable that will be looped over (int or fixed).
    :param array: a Python list or numpy array containing the values over which `a` will be looping. The spacing must be even in linear or logarithmic scales and it cannot be a QUA array.
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua._dsl.for_.
    """

    # Check for array length
    if len(array) == 0:
        raise Exception("The array must be of length > 0.")
    # Check QUA vs python variables
    if not isinstance(var, _Expression):
        raise Exception("The first argument must be a QUA variable.")
    if (not isinstance(array[0], (np.generic, int, float))) or (
        isinstance(array[0], bool)
    ):
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
    var_type = _get_qua_variable_type(var)
    start = array[0]
    stop = array[-1]
    # Linear increment
    if increment == "lin":
        step = array[1] - array[0]

        if var_type == "int":
            # Check that the array is an array of int with integer increments
            if (
                not float(step).is_integer()
                or not float(start).is_integer()
                or not float(stop).is_integer()
            ):
                raise Exception(
                    "When looping over a QUA int variable, the step and array elements must be integers."
                )
            # Generate the loop parameters for positive and negative steps
            if step > 0:
                return var, int(start), var <= int(stop), var + int(step)
            else:
                return var, int(start), var >= int(stop), var + int(step)

        elif var_type == "fixed":
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

        if var_type == "int":

            warnings.warn(
                "When using logarithmic increments with QUA integers, the resulting values will slightly differ from the ones in numpy.logspace() because of rounding errors. \n Please use the get_equivalent_log_array() function to get the exact values taken by the QUA variable and note that the number of points may also change."
            )
            if step > 1:
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

        elif var_type == "fixed":
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
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua._dsl.for_.
    """
    # Check QUA vs python variables
    if not isinstance(var, _Expression):
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
            raise Exception(
                "The required accuracy is to large:N * (2 ** -28) > step/2, please contact a QM member."
            )

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
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua._dsl.for_.
    """
    # Check QUA vs python variables
    if not isinstance(var, _Expression):
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
    :return: QUA for_ loop parameters (var, init, cond, update) as defined in https://qm-docs.qualang.io/api_references/qua/dsl_main?highlight=for_#qm.qua._dsl.for_.
    """
    # Check QUA vs python variables
    if not isinstance(var, _Expression):
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
    var_type = _get_qua_variable_type(var)
    if var_type == "int":
        warnings.warn(
            "When using logarithmic increments with QUA integers, the resulting values will slightly differ from the ones in numpy.logspace() because of rounding errors. \n Please use the get_equivalent_log_array() function to get the exact values taken by the QUA variable and note that the number of points may also change."
        )
        if step > 1:
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
    elif var_type == "fixed":
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
        while aprev < log_array[-1]:
            a_log.append(aprev)
            aprev = int(aprev * step)
    else:
        while aprev > log_array[-1]:
            a_log.append(aprev)
            aprev = int(aprev * step)
    return np.array(a_log)


def _get_qua_variable_type(variable):
    from qm.qua._dsl import _get_root_program_scope

    scope = _get_root_program_scope()
    variable_type = None
    for var in list(scope._program._program.script.variables):
        if var.name == variable._exp.variable.name:
            variable_type = var.type
    if variable_type == 0:
        return "int"
    elif variable_type == 1:
        return "bool"
    elif variable_type == 2:
        return "fixed"
