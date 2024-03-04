import pytest

from qualang_tools.loops import *
from qm.qua import *


@pytest.mark.parametrize(
    "arange_param",
    [
        [-0.05, -1, -0.15],
        [10, 20, 1],
        [20, 71, 2],
        [20, 71, 1],
        [11, 0, -1],
        [-11, -100, -2],
        [0.1, 1, 0.2],
        [0, 1, 0.2],
        [0, 2, 0.0001],
        [-1, 2, 0.00011],
        [-1, 1, 0.2],
        [0.00015, 1, 0.0001],
        [0, -2, -0.001],
    ],
)
def test_qua_arange(arange_param):
    if float(arange_param[2]).is_integer():
        with program() as prog:
            a = declare(int)
            a_st = declare_stream()
            with for_(*qua_arange(a, arange_param[0], arange_param[1], arange_param[2])):
                update_frequency("resonator", a)
                play("readout", "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")
    else:
        with program() as prog:
            a = declare(fixed)
            a_st = declare_stream()
            with for_(*qua_arange(a, arange_param[0], arange_param[1], arange_param[2])):
                play("readout" * amp(a), "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")


@pytest.mark.parametrize(
    "list_param",
    [
        [np.logspace(np.log10(50), np.log10(12500), 19), "int"],
        [np.logspace(np.log10(50000), np.log10(33), 72), "int"],
        [np.logspace(6, 4, 19), "int"],
        [np.logspace(3, 6, 199), "int"],
        [np.logspace(-3, 0, 99), "fixed"],
        [np.logspace(-3.5, -1, 11), "fixed"],
        [np.logspace(0.5, -0.5, 22), "fixed"],
        [np.logspace(0.5, -3.5, 21), "fixed"],
        [np.arange(-7.0547, -2.2141, 0.1015), "fixed"],
        [np.arange(-0.05, -1, -0.15), "fixed"],
        [np.arange(-1, 2, 0.0006), "fixed"],
        [np.arange(-11, -100, -2), "int"],
        [np.arange(20, 71, 2), "int"],
        [np.linspace(20, 71, 52), "int"],
        [np.linspace(0.1, 1, 6), "fixed"],
        [np.arange(10, 20, 1), "int"],
        [np.arange(20, 71, 1), "int"],
        [np.arange(0, 71, 2), "int"],
        [np.arange(0, 1, 0.1), "fixed"],
        [np.arange(0, 1, 0.2), "fixed"],
        [np.arange(0.1, 1, 0.2), "fixed"],
    ],
)
def test_from_array(list_param):
    if list_param[1] == "int":
        with program() as prog:
            a = declare(int)
            a_st = declare_stream()
            with for_(*from_array(a, list_param[0])):
                update_frequency("resonator", a)
                play("readout", "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")
    else:
        with program() as prog:
            a = declare(fixed)
            a_st = declare_stream()
            with for_(*from_array(a, list_param[0])):
                play("readout" * amp(a), "resonator")
                save(a, a_st)
            with stream_processing():
                a_st.save_all("a")


@pytest.mark.parametrize(
    "linspace_param",
    [
        [0.1, 1, 5],
        [0.1, 0.95, 5],
        [-1, 0, 2],
        [-1, 1, 2],
        [-8, 7, 51],
        [-0.1, 0.1, 5000],
        [-1, 2, 11],
    ],
)
def test_qua_linspace(linspace_param):
    with program() as prog:
        a = declare(fixed)
        a_st = declare_stream()
        with for_(*qua_linspace(a, linspace_param[0], linspace_param[1], linspace_param[2])):
            play("readout" * amp(a), "resonator")
            save(a, a_st)
        with stream_processing():
            a_st.save_all("a")


@pytest.mark.parametrize(
    "logspace_param",
    [
        [0.5, -2, 24],
        [0, -3, 51],
        [0, -3, 50],
        [-4, 0.5, 11],
        [-3.8, 0.2, 7],
    ],
)
def test_qua_logspace_fixed(logspace_param):
    with program() as prog:
        a = declare(fixed)
        a_st = declare_stream()
        with for_(*qua_logspace(a, logspace_param[0], logspace_param[1], logspace_param[2])):
            play("readout" * amp(a), "resonator")
            save(a, a_st)
        with stream_processing():
            a_st.save_all("a")


@pytest.mark.parametrize(
    "logspace_param",
    [
        [np.log10(500), np.log10(12500), 11],
        [np.log10(5000), np.log10(125), 30],
        [np.log10(40), np.log10(1001), 51],
    ],
)
def test_qua_logspace_int(logspace_param):
    with program() as prog:
        t = declare(int)
        t_st = declare_stream()
        with for_(*qua_logspace(t, logspace_param[0], logspace_param[1], logspace_param[2])):
            play("readout", "resonator", duration=t)
            save(t, t_st)
        with stream_processing():
            t_st.save_all("a")
