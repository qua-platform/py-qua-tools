import numpy as np
from qm import generate_qua_script

from qm.qua import program, declare_with_stream, assign, fixed
from qm.qua.extensions.qua_iterators import QuaIterable, NativeIterable, QuaIterableRange, QuaProduct, NativeIterableRange, QuaZip

from qualang_tools.loops.qua_iterable_postprocess import fetch_xarray_data
from tests.tests_qua_utilities.conftest import config
from tests.tests_qua_utilities.fetch_xarray_helpers import (
    simulation_config, frequencies, qubits,
)


def test_qua_zip_native(qmm):
    native_zip_values = ["q1", "q2", "q3"]
    prod = QuaProduct([
        QuaIterableRange("shot", 10),
        QuaZip([
            NativeIterable("qubit", native_zip_values),
            NativeIterableRange("amp", 0.1, 0.4, 0.1),
        ], name="qb_amp"),
        QuaIterable("frequency", frequencies),
    ])
    with program() as prog:
        for args in prod:
            s = declare_with_stream(int, "val_st")
            assign(s, args.shot)

    print(generate_qua_script(prog))
    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["val_st"].dims == ("shot", "qb_amp", "frequency"), f"val_st dims: expected ('shot', 'qb_amp', 'frequency'), got {xarray_data['val_st'].dims}"
    assert xarray_data["val_st"].shape == (10, len(native_zip_values), len(frequencies)), f"val_st shape: expected {(10, len(native_zip_values), len(frequencies))}, got {xarray_data['val_st'].shape}"

    for i in range(10):
        assert (xarray_data["val_st"][i] == i).all(), f"val_st[{i}]: expected all values to be {i}, got {xarray_data['val_st'][i].values}"


def test_qua_zip_qua(qmm):
    tau_values = np.linspace(1, 7, 5)
    prod = QuaProduct([
        QuaZip([
            QuaIterable("frequency", frequencies),
            QuaIterable("tau", tau_values),
        ], name="freq_tau"),
        NativeIterable("qubit", qubits),
    ])
    with program() as prog:
        for args in prod:
            s = declare_with_stream(fixed, "freq_st")
            assign(s, args.freq_tau.frequency)

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["freq_st"].dims == ("freq_tau", "qubit"), f"freq_st dims: expected ('freq_tau', 'qubit'), got {xarray_data['freq_st'].dims}"
    assert xarray_data["freq_st"].shape == (len(frequencies), len(qubits)), f"freq_st shape: expected {(len(frequencies), len(qubits))}, got {xarray_data['freq_st'].shape}"

    for i, f in enumerate(frequencies):
        assert np.allclose(xarray_data["freq_st"][i], f), f"freq_st[{i}]: expected all values to be {f}, got {xarray_data['freq_st'][i].values}"
