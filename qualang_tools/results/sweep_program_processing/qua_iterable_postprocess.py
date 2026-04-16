from typing import Optional, Sequence, Union
from itertools import product
import numpy as np
import xarray as xr

from qm.api.v2.job_api.job_api import JobApi
from qm.qua.extensions.qua_iterators.qua_iterators_base import IterableBase
from qm.qua.extensions.qua_iterators import QuaProduct
from qm.qua._dsl.stream_processing.direct_stream_processing import STREAM_NAME_SEPARATOR


def _native_column_indices(itr: IterableBase) -> list[int]:
    """Get the stream-suffix indices for a native iterable.

    Stream names use the index of the native iteration, not the value.
    """
    return list(range(len(itr)))


def _clean_result_value(
    value: Union[np.ndarray, Optional[np.floating], Optional[np.integer]],
) -> np.ndarray:
    """Extract a clean numpy array from a single fetch_results value.

    Handles structured arrays (e.g. from dual_demod) by extracting the "value"
    field, and wraps numpy scalars into arrays.
    """
    if isinstance(value, np.ndarray):
        if isinstance(value[0], np.void):
            return value["value"]
        return value
    return np.array(value)


def _find_stream_name_from_full_stream_name(result_name, native_columns):
    for native_names in product(*native_columns):
        suffix = STREAM_NAME_SEPARATOR + STREAM_NAME_SEPARATOR.join(str(n) for n in native_names)
        if result_name.endswith(suffix):
            stream_name = result_name[: -len(suffix)]

            return stream_name, native_names

    raise ValueError(f"No native iterator match found in '{result_name}'")


def _extract_stream_data_from_sweep_with_native_iterables(results, sweep_iterables, native_itr):
    native_columns = [_native_column_indices(itr) for itr in native_itr]
    stream_data = {}
    stream_with_native_itr = {}
    for res_name, value in results.items():
        clean_value = _clean_result_value(value)
        stream_name, native_names = _find_stream_name_from_full_stream_name(res_name, native_columns)
        d = stream_with_native_itr.setdefault(stream_name, {})
        d[native_names] = clean_value

    # Assemble native iterator results into nd-arrays with correct axis ordering
    native_shape = tuple(len(col) for col in native_columns)

    for stream_name, combos in stream_with_native_itr.items():
        sorted_keys = list(product(*native_columns))
        arrays = [combos[key] for key in sorted_keys]
        stacked = np.array(arrays)

        # Reshape flat combo dimension into native grid: (*native_dims, *non_native_dims)
        non_avg_itr = [itr for itr in sweep_iterables if not itr.is_stream_averaged(stream_name)]
        non_native_shape = arrays[0].shape
        expected_non_native_shape = tuple([itr.buffer_size for itr in non_avg_itr if itr.is_qua_iterable])

        if len(expected_non_native_shape) > 0:
            if tuple(non_native_shape) != tuple(expected_non_native_shape):
                raise ValueError(f"Expected qua iterators shape {expected_non_native_shape} got {non_native_shape}")
            result = stacked.reshape(*native_shape, *non_native_shape)
        else:
            result = stacked.reshape(*native_shape)

        # Transpose so each dim sits at its original sweep position (among non-averaged only)
        # Current order after reshape: all native first, then non-native non-averaged
        current_order = native_itr + [itr for itr in non_avg_itr if itr.is_qua_iterable]
        perm = [current_order.index(itr) for itr in non_avg_itr]
        stream_data[stream_name] = np.transpose(result, perm)

    return stream_data


def fetch_xarray_data(
    job: JobApi,
    sweep: Union[QuaProduct, Sequence[IterableBase]],
    wait_until_done: bool = False,
) -> xr.Dataset:
    """Fetch job results and organize them into an xarray Dataset aligned with sweep dimensions.

    Retrieves all result streams from a completed QUA job and reshapes them according to
    the sweep structure (product of iterables). Native iterables are reassembled from their
    per-index streams into nd-arrays, and axes are transposed to match the original sweep
    order. Each data variable in the returned Dataset is indexed only by the dimensions
    that were not stream-averaged for that variable. Coordinate metadata (e.g. units) from
    the iterables is attached to the corresponding Dataset coordinates.

    Args:
        job: A completed QUA job from which to fetch results.
        sweep: The sweep definition used in the QUA program — either a ``QuaProduct``
            or a sequence of ``IterableBase`` objects.
        wait_until_done: If True, block until the job completes before fetching results.
            Defaults to False.

    Returns:
        An ``xr.Dataset`` where each data variable corresponds to a result stream,
        dimensioned by the non-averaged sweep iterables, with coordinates and metadata
        derived from the sweep definition.

    Raises:
        ValueError: If a result stream name cannot be matched to the expected native
            iterator suffixes, or if the non-native shape of a stream does not match
            the expected shape from the sweep iterables.
    """
    sweep_iterables = sweep.iterables if isinstance(sweep, QuaProduct) else sweep
    native_itr = [itr for itr in sweep_iterables if not itr.is_qua_iterable]

    results = job.result_handles.fetch_results(wait_until_done=wait_until_done)
    if native_itr:
        stream_data = _extract_stream_data_from_sweep_with_native_iterables(results, sweep_iterables, native_itr)
    else:
        stream_data = {}
        for res_name, value in results.items():
            stream_data[res_name] = _clean_result_value(value)

    # Build xarray Dataset — select only non-averaged dims per stream
    all_coords = {}
    for itr in sweep_iterables:
        if isinstance(itr.values[0], tuple):
            coord = np.empty(len(itr.values), dtype=object)
            coord[:] = itr.values
            all_coords[itr.name] = coord
        else:
            all_coords[itr.name] = list(itr.values)

    data_vars = {}
    used_dims = set()
    for name, arr in stream_data.items():
        stream_dims = [itr.name for itr in sweep_iterables if not itr.is_stream_averaged(name)]
        data_vars[name] = (stream_dims, arr)
        used_dims.update(stream_dims)

    coords = {k: v for k, v in all_coords.items() if k in used_dims}
    ds = xr.Dataset(data_vars, coords=coords)
    for itr in sweep_iterables:
        unit = itr.metadata.get("unit", None)
        if unit is not None and itr.name in ds.coords:
            ds.coords[itr.name].attrs["unit"] = unit
    return ds
