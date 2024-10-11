from dataclasses import asdict

from qualang_tools.wirer.instruments import Instruments
import pytest


def pytest_configure():
    pytest.visualize_flag = True
    pytest.channels_are_equal = lambda x, y: type(x) == type(y) and asdict(x) == asdict(y)


@pytest.fixture(params=["lf-fem", "opx+"])
def instruments_qw_soprano(request) -> Instruments:
    print(request.param)
    instruments = Instruments()
    if request.param == "lf-fem":
        instruments.add_lf_fem(controller=1, slots=[1, 2, 3])
    elif request.param == "opx+":
        instruments.add_opx_plus(controllers=[1, 2])
    instruments.add_octave(indices=[1, 2])
    return instruments


@pytest.fixture(params=["opx+"])
def instruments_1opx_1octave(request) -> Instruments:
    instruments = Instruments()
    if request.param == "lf-fem":
        instruments.add_lf_fem(controller=1, slots=[1])
    elif request.param == "opx+":
        instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)
    return instruments


@pytest.fixture(params=["lf-fem"])  # , "opx+"])
def instruments_1octave(request) -> Instruments:
    instruments = Instruments()
    if request.param == "lf-fem":
        instruments.add_lf_fem(controller=1, slots=[1, 2])
    elif request.param == "opx+":
        instruments.add_opx_plus(controllers=[1])
    instruments.add_octave(indices=1)
    return instruments


@pytest.fixture()
def instruments_2lf_2mw() -> Instruments:
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=[1, 2])
    instruments.add_mw_fem(controller=1, slots=[3, 7])
    return instruments
