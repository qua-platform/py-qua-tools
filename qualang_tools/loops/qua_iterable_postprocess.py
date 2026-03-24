from typing import Sequence, Union
from itertools import product
import numpy as np
import pandas as pd
import xarray as xr

from qm.api.v2.job_api.job_api import JobApiWithDeprecations
from qm.qua.extensions.qua_iterators.qua_iterators_base import IterableBase
from qm.qua.extensions.qua_iterators.qua_native_iterators import NativeIterableBase
from qm.qua.extensions.qua_iterators import QuaProduct
from qm.qua.extensions.qua_iterators.qua_zip import QuaZip, NativeZipIterable
from qm.qua._dsl.stream_processing.direct_stream_processing import STREAM_NAME_SEPARATOR


def _is_native(itr: IterableBase) -> bool:
    """Check if an iterable behaves as a native iterable for stream name purposes."""
    if isinstance(itr, NativeIterableBase):
        return True
    if isinstance(itr, QuaZip) and isinstance(itr.zip_iterable, NativeZipIterable):
        return True
    return False


def _native_column_indices(itr: IterableBase) -> list:
    """Get the stream-suffix indices for a native iterable.

    Stream names use the index of the native iteration, not the value.
    """
    return list(range(len(itr)))


def fetch_xarray_data(
    job: JobApiWithDeprecations, sweep: Union[QuaProduct, Sequence[IterableBase]]
) -> xr.Dataset:
    sweep_iterables = sweep.iterables if isinstance(sweep, QuaProduct) else sweep
    native_itr = [itr for itr in sweep_iterables if _is_native(itr)]
    native_columns = [_native_column_indices(itr) for itr in native_itr]

    stream_data = {}  # {stream_name: {native_combo: value}}
    stream_with_native_itr = {}
    results = job.result_handles.fetch_results()

    for res_name, value in results.items():
        if isinstance(value, np.ndarray):
            if isinstance(value[0], np.void):
                clean_value = value[0]["value"]
            else:
                clean_value = value
        else:
            clean_value = np.array(value)

        if native_columns:
            for native_names in product(*native_columns):
                suffix = STREAM_NAME_SEPARATOR + STREAM_NAME_SEPARATOR.join(str(n) for n in native_names)
                if res_name.endswith(suffix):
                    stream_name = res_name[: -len(suffix)]
                    d = stream_with_native_itr.setdefault(stream_name, {})
                    d[native_names] = clean_value
                    break
            else:
                raise ValueError(
                    f"No native iterator match found in '{res_name}'"
                )
        else:
            stream_data[res_name] = clean_value

    # Assemble native iterator results into nd-arrays with correct axis ordering
    native_shape = tuple(len(col) for col in native_columns)

    for stream_name, combos in stream_with_native_itr.items():
        sorted_keys = list(product(*native_columns))
        arrays = [combos[key] for key in sorted_keys]
        stacked = np.array(arrays)

        # Reshape flat combo dimension into native grid: (*native_dims, *non_native_dims)
        non_native_shape = arrays[0].shape
        result = stacked.reshape(*native_shape, *non_native_shape)

        # Transpose so each dim sits at its original sweep position (among non-averaged only)
        non_avg_itr = [itr for itr in sweep_iterables if not itr.is_stream_averaged(stream_name)]

        expected_non_native_shape = tuple([itr.buffer_size for itr in non_avg_itr if not _is_native(itr)])
        if tuple(non_native_shape) != tuple(expected_non_native_shape):
            raise ValueError(f"Expected qua iterators shape {expected_non_native_shape} got {non_native_shape}")

        # Current order after reshape: all native first, then non-native non-averaged
        current_order = native_itr + [itr for itr in non_avg_itr if not _is_native(itr)]
        perm = [current_order.index(itr) for itr in non_avg_itr]

        stream_data[stream_name] = np.transpose(result, perm)

    # Build xarray Dataset — select only non-averaged dims per stream
    all_coords = {}
    for itr in sweep_iterables:
        if isinstance(itr, QuaZip):
            vals = list(itr.values())
            sub_names = [sub.name for sub in itr.zip_iterable._iterables]
            all_coords[itr.name] = pd.MultiIndex.from_tuples(vals, names=sub_names)
        else:
            all_coords[itr.name] = list(itr.values())

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
