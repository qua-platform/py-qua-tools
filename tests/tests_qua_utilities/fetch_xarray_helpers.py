from typing import Sequence, Union

import numpy as np
import xarray as xr

from qm.qua.extensions.qua_iterators import QuaIterable, NativeIterable, QuaIterableRange, QuaProduct, NativeIterableRange
from qm.qua.extensions.qua_iterators.qua_iterators_base import IterableBase
from qm import SimulationConfig, LoopbackInterface

from qualang_tools.loops.qua_iterable_postprocess import fetch_xarray_data
from tests.tests_qua_utilities.conftest import config


simulation_config = SimulationConfig(50000, simulation_interface=LoopbackInterface([("con1", 2, 8, "con1", 2, 1)]))

shots = 100
frequencies = np.linspace(1, 2, 5)
amp_start = 1.1
amp_stop = 4
amp_step = 2
amp_values = np.arange(amp_start, amp_stop, amp_step)
qubits = ["q1", "q2", "q3"]


def make_product():
    return QuaProduct([
        QuaIterableRange("shot", shots),
        NativeIterable("qubit", qubits),
        QuaIterable("frequency", frequencies),
        NativeIterableRange("amp", amp_start, amp_stop, amp_step)
    ])


def simulate_and_fetch(
    qmm, prog, sweep: Union[QuaProduct, Sequence[IterableBase]],
) -> xr.Dataset:
    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    return fetch_xarray_data(job, sweep)


def assert_dims_and_shape(
    ds: xr.Dataset, var_name: str, expected_dims: tuple[str, ...], expected_shape: tuple[int, ...],
):
    assert ds[var_name].dims == expected_dims, (
        f"{var_name} dims: expected {expected_dims}, got {ds[var_name].dims}"
    )
    assert ds[var_name].shape == expected_shape, (
        f"{var_name} shape: expected {expected_shape}, got {ds[var_name].shape}"
    )


def assert_allclose_sel(
    ds: xr.Dataset, var_name: str, expected, **sel_kwargs,
):
    actual = ds[var_name].sel(**sel_kwargs)
    sel_str = ", ".join(f"{k}={v}" for k, v in sel_kwargs.items())
    assert np.allclose(actual, expected), (
        f"{var_name}({sel_str}): expected {expected}, got {actual.values}"
    )
