from qm.qua import *


def assign_variables_to_element(element, *variables):
    """
    Forces the given variables to be used by the given element thread. Useful as a workaround for when the compiler
    wrongly assigns variables which can causes gaps.
    """
    _exp = Cast.to_int(variables[0])
    for variable in variables[1:]:
        _exp += Cast.to_int(variable)
    wait(4 + 0 * _exp, element)
