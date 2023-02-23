from qm.qua import *


def assign_variables_to_element(element, *variables):
    """
    Forces the given variables to be used by the given element thread. Useful as a workaround for when the compiler
    wrongly assigns variables which can cause gaps.
    To be used at the beginning of a program, will add a 16ns wait to the given element. Use an `align()` if needed.

    Example::

        >>> with program() as program_name:
        >>>     a = declare(int)
        >>>     b = declare(fixed)
        >>>     assign_variables_to_element('resonator', a, b)
        >>>     align()
        >>>     ...

    """
    _exp = Cast.to_int(variables[0])
    for variable in variables[1:]:
        _exp += Cast.to_int(variable)
    wait(4 + 0 * _exp, element)
