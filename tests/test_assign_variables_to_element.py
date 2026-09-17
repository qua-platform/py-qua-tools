from qm.qua import program, declare, fixed

from qualang_tools.addons.variables import assign_variables_to_element


def test_assign_variables_to_element_compiles_in_program():
    with program() as prog:
        a = declare(int)
        b = declare(fixed)
        assign_variables_to_element("resonator", a, b)

    assert prog is not None
