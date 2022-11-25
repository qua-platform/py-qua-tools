import pytest

#  modules needed for testing

from qm.qua import program, for_, declare
from qualang_tools import units

# testing interference with other context managers
from contextlib import contextmanager


@contextmanager
def DummyContextManager():
    try:
        yield
    finally:
        pass


@pytest.fixture
def unit():
    return units.unit(coerce_to_integer=False)


@pytest.fixture
def unit_verbose():
    return units.unit(coerce_to_integer=True, verbose=True)


def test_not_in_scope(unit):

    assert unit.ns == 1
    assert unit.us == 1e3
    assert unit.ms == 1e6
    assert unit.s == 1e9
    assert unit.clock_cycle == 4


def test_in_scope(unit):

    with program() as dummyprogram:
        assert unit.ns == 1 / 4
        assert unit.us == 1e3 / 4
        assert unit.ms == 1e6 / 4
        assert unit.s == 1e9 / 4
        assert unit.clock_cycle == 1


def test_nested(unit):

    with program() as dummyprogram:

        ind = declare(int)

        with for_(ind, 0, ind < 10, ind + 1):
            assert unit.ns == 1 / 4
            assert unit.us == 1e3 / 4
            assert unit.ms == 1e6 / 4
            assert unit.s == 1e9 / 4
            assert unit.clock_cycle == 1


def test_nested_contexts(unit):

    with DummyContextManager():

        with program() as dummyprogram:
            assert unit.ns == 1 / 4
            assert unit.us == 1e3 / 4
            assert unit.ms == 1e6 / 4
            assert unit.s == 1e9 / 4
            assert unit.clock_cycle == 1


def test_other_context(unit):

    with DummyContextManager():

        assert unit.ns == 1
        assert unit.us == 1e3
        assert unit.ms == 1e6
        assert unit.s == 1e9
        assert unit.clock_cycle == 4


def _subroutine_in_scope(unit):

    assert unit.ns == 1 / 4
    assert unit.us == 1e3 / 4
    assert unit.ms == 1e6 / 4
    assert unit.s == 1e9 / 4
    assert unit.clock_cycle == 1


def test_in_scope_subroutine(unit):

    with program() as dummyprogram:
        _subroutine_in_scope(unit)


def _subroutine_not_in_scope(unit):

    assert unit.ns == 1
    assert unit.us == 1e3
    assert unit.ms == 1e6
    assert unit.s == 1e9
    assert unit.clock_cycle == 4


def test_not_in_scope_subroutine(unit):

    _subroutine_not_in_scope(unit)


# Test the integer coercion


def test_not_in_scope_verbose(unit_verbose):

    assert unit_verbose.ns == 1
    assert unit_verbose.us == 1e3
    assert unit_verbose.ms == 1e6
    assert unit_verbose.s == 1e9
    assert unit_verbose.clock_cycle == 4


def test_in_scope_verbose(unit_verbose):

    with program() as dummyprogram:
        assert 4 * unit_verbose.ns == 1
        assert 4 * unit_verbose.us == 1e3
        assert 4 * unit_verbose.ms == 1e6
        assert 4 * unit_verbose.s == 1e9
        assert unit_verbose.clock_cycle == 1


def test_in_scope_verbose_rmul(unit_verbose):

    with program() as dummyprogram:
        assert unit_verbose.ns * 4 == 1
        assert unit_verbose.us * 4 == 1e3
        assert unit_verbose.ms * 4 == 1e6
        assert unit_verbose.s * 4 == 1e9
        assert unit_verbose.clock_cycle == 1


def test_in_scope_verbose_warnings(unit_verbose):

    with program() as dummyprogram:
        with pytest.warns(RuntimeWarning):
            assert 6 * unit_verbose.ns == 1
        with pytest.warns(RuntimeWarning):
            assert (4 / 3) * unit_verbose.us == int(1 / 3 * 1e3)
        with pytest.warns(RuntimeWarning):
            assert (4 / 3) * unit_verbose.ms == int(1 / 3 * 1e6)
        with pytest.warns(RuntimeWarning):
            assert (4 / 3) * unit_verbose.s == int(1 / 3 * 1e9)
