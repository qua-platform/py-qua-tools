import pytest

from marshmallow.warnings import RemovedInMarshmallow4Warning
#  modules needed for testing
with pytest.warns(RemovedInMarshmallow4Warning):
    # will avoid raising warnings from qua testing the timing feature
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
    return units.unit()

def test_not_in_scope(unit):

    assert unit.ns == 1
    assert unit.us == 1e3
    assert unit.ms == 1e6
    assert unit.s  == 1e9
    assert unit.clock_cycle == 4

def test_in_scope(unit):

    with program() as dummyprogram:
        assert unit.ns == 1/4
        assert unit.us == 1e3/4
        assert unit.ms == 1e6/4
        assert unit.s  == 1e9/4
        assert unit.clock_cycle == 1

def test_nested(unit):

    with program() as dummyprogram:

        ind = declare(int)

        with for_(ind, 0, ind < 10, ind + 1):
            assert unit.ns == 1/4
            assert unit.us == 1e3/4
            assert unit.ms == 1e6/4
            assert unit.s  == 1e9/4
            assert unit.clock_cycle == 1

def test_nested_contexts(unit):

    with DummyContextManager():

        with program() as dummyprogram:
            assert unit.ns == 1/4
            assert unit.us == 1e3/4
            assert unit.ms == 1e6/4
            assert unit.s  == 1e9/4
            assert unit.clock_cycle == 1

def test_other_context(unit):

    with DummyContextManager():

        assert unit.ns == 1
        assert unit.us == 1e3
        assert unit.ms == 1e6
        assert unit.s  == 1e9
        assert unit.clock_cycle == 4

def _subroutine_in_scope(unit):

    assert unit.ns == 1/4
    assert unit.us == 1e3/4
    assert unit.ms == 1e6/4
    assert unit.s  == 1e9/4
    assert unit.clock_cycle == 1

def test_in_scope_subroutine(unit):

    with program() as dummyprogram:
        _subroutine_in_scope(unit)

def _subroutine_not_in_scope(unit):

    assert unit.ns == 1
    assert unit.us == 1e3
    assert unit.ms == 1e6
    assert unit.s  == 1e9
    assert unit.clock_cycle == 4

def test_not_in_scope_subroutine(unit):

    _subroutine_not_in_scope(unit)
