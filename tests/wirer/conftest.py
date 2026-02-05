from dataclasses import asdict

from qualang_tools.wirer.instruments import Instruments
import pytest
import random


def pytest_configure():
    pytest.visualize_flag = False
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


@pytest.fixture()
def instruments_2mw() -> Instruments:
    instruments = Instruments()
    instruments.add_mw_fem(controller=1, slots=[1, 2])
    return instruments


@pytest.fixture()
def instruments_1opx_2external_mixer() -> Instruments:
    instruments = Instruments()
    instruments.add_opx_plus(controllers=[1])
    instruments.add_external_mixer(indices=[1, 2])
    return instruments


@pytest.fixture()
def instruments_5opx1000() -> Instruments:
    instruments = Instruments()
    instruments.add_lf_fem(controller=1, slots=[1, 2])
    instruments.add_lf_fem(controller=2, slots=[1, 2])
    instruments.add_lf_fem(controller=3, slots=[1, 2])
    instruments.add_lf_fem(controller=4, slots=[1, 2])
    instruments.add_mw_fem(controller=5, slots=[3, 7])
    instruments.add_octave(indices=[1, 2])
    return instruments


@pytest.fixture()
def instruments_stacked_9opx1000() -> Instruments:
    # take a specific random seed for reproducibility
    random.seed(1337)
    instruments = Instruments()

    # All possible slot numbers (1-8)
    all_slots = list(range(1, 9))  # [1, 2, 3, 4, 5, 6, 7, 8]

    # For each controller 1-9
    for controller in range(1, 10):
        # Get 8 random slots (all slots shuffled)
        controller_slots = all_slots.copy()
        random.shuffle(controller_slots)

        # Assign first 3 slots to LF-FEMs
        lf_slots = controller_slots[:3]
        instruments.add_lf_fem(controller=controller, slots=lf_slots)

        # Assign next 5 slots to MW-FEMs
        mw_slots = controller_slots[3:8]
        instruments.add_mw_fem(controller=controller, slots=mw_slots)

    return instruments

