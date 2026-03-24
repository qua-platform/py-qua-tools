import numpy as np
import pytest

from qm.qua import program, declare_with_stream, measure, dual_demod, assign, fixed
from qm.qua.extensions.qua_iterators import QuaIterable, NativeIterable, QuaIterableRange, QuaProduct, NativeIterableRange

from qualang_tools.loops.qua_iterable_postprocess import fetch_xarray_data
from tests.tests_qua_utilities.conftest import config
from tests.tests_qua_utilities.fetch_xarray_helpers import (
    simulation_config, frequencies, amp_start, amp_stop, amp_step, make_product,
)


def test_multi_save_raises(qmm):
    prod = make_product()
    with program() as prog:
        for args in prod:
            multi_save = declare_with_stream(int, "shot_st_multi_save")
            assign(multi_save, args.shot)
            assign(multi_save, args.shot + 1)

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()

    with pytest.raises(ValueError, match="Expected qua iterators shape"):
        fetch_xarray_data(job, prod)


def test_demod_np_void(qmm):
    """Test np.void value handling from dual_demod measurement results."""
    prod = QuaProduct([
        QuaIterableRange("shot", 10),
        NativeIterable("qubit", ["q1"]),
    ])
    with program() as prog:
        for args in prod:
            I = declare_with_stream(fixed, "I_st")
            measure("readout", "resonator", None, dual_demod.full("cos", "sin", I))

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["I_st"].dims == ("shot", "qubit"), f"I_st dims: expected ('shot', 'qubit'), got {xarray_data['I_st'].dims}"
    assert xarray_data["I_st"].shape == (10, 1), f"I_st shape: expected (10, 1), got {xarray_data['I_st'].shape}"


def test_units_metadata(qmm):
    prod = QuaProduct([
        QuaIterableRange("shot", 10, metadata={"unit": "count"}),
        NativeIterable("qubit", ["q1"], metadata={"unit": "qubit_id"}),
        QuaIterable("frequency", frequencies, metadata={"unit": "Hz"}),
        NativeIterableRange("amp", amp_start, amp_stop, amp_step, metadata={"unit": "V"})
    ])
    with program() as prog:
        for args in prod:
            s = declare_with_stream(float, "val_st", average_axes=["shot"])
            assign(s, args.frequency)

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data.coords["frequency"].attrs["unit"] == "Hz", f"frequency unit: expected 'Hz', got {xarray_data.coords['frequency'].attrs.get('unit')}"
    assert xarray_data.coords["amp"].attrs["unit"] == "V", f"amp unit: expected 'V', got {xarray_data.coords['amp'].attrs.get('unit')}"
    assert xarray_data.coords["qubit"].attrs["unit"] == "qubit_id", f"qubit unit: expected 'qubit_id', got {xarray_data.coords['qubit'].attrs.get('unit')}"

    # shot is averaged out — its unit should not be set on any coord
    assert "shot" not in xarray_data.coords, f"'shot' should not be in coords after averaging, got {list(xarray_data.coords)}"
