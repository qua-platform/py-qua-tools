import numpy as np
import pytest
from qm.qua import program, declare, fixed

from qualang_tools.loops import from_array, qua_arange, qua_linspace, qua_logspace, get_equivalent_log_array


def test_from_array_empty_raises():
    with program():
        a = declare(int)
        with pytest.raises(Exception, match="length > 0"):
            from_array(a, [])


def test_from_array_not_qua_variable_raises():
    with program():
        with pytest.raises(Exception, match="QUA variable"):
            from_array(0, [1, 2, 3])


def test_from_array_uneven_spacing_raises():
    with program():
        a = declare(int)
        with pytest.raises(Exception, match="even in linear or logarithmic"):
            from_array(a, np.array([1, 2, 4, 7]))


def test_from_array_int_requires_integer_step():
    with program():
        a = declare(int)
        with pytest.raises(Exception, match="must be integers"):
            from_array(a, [0.0, 0.5, 1.0])


def test_from_array_linear_int_returns_loop_params():
    with program():
        a = declare(int)
        var, start, _cond, _update = from_array(a, [10, 12, 14])
        assert var is a
        assert start == 10


def test_qua_arange_not_qua_variable_raises():
    with program():
        with pytest.raises(Exception, match="QUA variable"):
            qua_arange(1, 0, 10, 1)


def test_qua_arange_int_step_params():
    with program():
        a = declare(int)
        var, start, _cond, _update = qua_arange(a, 0, 10, 2)
        assert var is a
        assert start == 0


def test_qua_linspace_num_must_be_integer():
    with program():
        a = declare(fixed)
        with pytest.raises(Exception, match="python integer"):
            qua_linspace(a, 0.0, 1.0, 3.5)


def test_qua_logspace_num_must_be_positive():
    with program():
        a = declare(fixed)
        with pytest.raises(Exception, match="greater than 0"):
            qua_logspace(a, -1, 0, 0)


def test_get_equivalent_log_array_length():
    vector = np.logspace(np.log10(100), np.log10(10000), 10)
    equivalent = get_equivalent_log_array(vector)
    assert len(equivalent) >= 2
    assert equivalent[0] == round(vector[0])
