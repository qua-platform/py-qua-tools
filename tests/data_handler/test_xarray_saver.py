import copy
import pytest
import numpy as np
import xarray as xr
from qualang_tools.results.data_handler.data_processors import XarraySaver


def module_installed(module_name):
    try:
        exec(f"import {module_name}")
    except ImportError:
        return False
    return True


def dicts_equal(d1, d2):
    if d1.keys() != d2.keys():
        return False
    for key in d1:
        if key not in d2:
            return False
        elif isinstance(d1[key], dict):
            if not dicts_equal(d1[key], d2[key]):
                return False
        elif isinstance(d1[key], np.ndarray):
            if not np.array_equal(d1[key], d2[key]):
                return False
        elif isinstance(d1[key], xr.Dataset):
            if not d1[key].identical(d2[key]):
                return False
        else:
            if not bool(d1[key] == d2[key]):
                return False
    return True


@pytest.mark.skipif(not module_installed("xarray"), reason="xarray not installed")
def test_xarray_saver_no_xarrays():
    xarray_saver = XarraySaver()
    data = {"a": 1, "b": 2, "c": 3}
    assert xarray_saver.process(data) == data


@pytest.mark.skipif(not module_installed("xarray"), reason="xarray not installed")
def test_xarray_data_saver_suffixes():
    xarray_saver = XarraySaver()
    assert xarray_saver.file_format == "hdf5"
    assert xarray_saver.file_suffix == ".h5"

    xarray_saver = XarraySaver(file_format="hdf5")
    assert xarray_saver.file_suffix == ".h5"

    xarray_saver = XarraySaver(file_format="nc")
    assert xarray_saver.file_suffix == ".nc"

    xarray_saver = XarraySaver(file_format="netcdf")
    assert xarray_saver.file_suffix == ".nc"

    xarray_saver = XarraySaver(file_format="zarr")
    assert xarray_saver.file_suffix == ".zarr"


@pytest.mark.skipif(not (module_installed("xarray") and module_installed("netCDF4")), reason="xarray not installed")
def test_xarray_saver_merge_netcdf(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": xr.Dataset()}

    xarray_saver = XarraySaver(merge_arrays=True, file_format="nc")
    processed_data = xarray_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "c": "./xarrays.nc#c", "d": "./xarrays.nc#d"}

    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "xarrays.nc").exists()

    xr.load_dataset(tmp_path / "xarrays.nc", group="c")
    xr.load_dataset(tmp_path / "xarrays.nc", group="d")


@pytest.mark.skipif(not (module_installed("xarray") and module_installed("netCDF4")), reason="xarray not installed")
def test_xarray_saver_merge_hdf5(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": xr.Dataset()}

    xarray_saver = XarraySaver(merge_arrays=True, file_format="h5")
    processed_data = xarray_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "c": "./xarrays.h5#c", "d": "./xarrays.h5#d"}

    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "xarrays.h5").exists()

    xr.load_dataset(tmp_path / "xarrays.h5", group="c")
    xr.load_dataset(tmp_path / "xarrays.h5", group="d")


@pytest.mark.skipif(not module_installed("xarray"), reason="xarray not installed")
def test_xarray_saver_no_merge_netcdf(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": xr.Dataset()}

    xarray_saver = XarraySaver(merge_arrays=False)
    processed_data = xarray_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "c": "./c.h5", "d": "./d.h5"}

    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "c.h5").exists()
    assert (tmp_path / "d.h5").exists()

    xr.load_dataset(tmp_path / "c.h5")
    xr.load_dataset(tmp_path / "d.h5")


@pytest.mark.skipif(not module_installed("xarray"), reason="xarray not installed")
def test_xarray_saver_no_merge_hdf5_nested(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": {"d1": xr.Dataset()}}

    xarray_saver = XarraySaver(merge_arrays=False, file_format="nc")
    processed_data = xarray_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "c": "./c.nc", "d": {"d1": "./d.d1.nc"}}

    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "c.nc").exists()
    assert (tmp_path / "d.d1.nc").exists()

    xr.load_dataset(tmp_path / "c.nc")
    xr.load_dataset(tmp_path / "d.d1.nc")


@pytest.mark.skipif(not (module_installed("xarray") and module_installed("netCDF4")), reason="xarray not installed")
def test_xarray_saver_merge_hdf5_nested(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": {"d1": xr.Dataset()}}

    xarray_saver = XarraySaver(merge_arrays=True, file_format="nc")
    processed_data = xarray_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "c": "./xarrays.nc#c", "d": {"d1": "./xarrays.nc#d.d1"}}
    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "xarrays.nc").exists()

    xr.load_dataset(tmp_path / "xarrays.nc", group="c")
    xr.load_dataset(tmp_path / "xarrays.nc", group="d.d1")


@pytest.mark.skipif(not module_installed("xarray"), reason="xarray not installed")
def test_xarray_saver_does_not_affect_data():
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": {"d1": xr.Dataset()}}
    deepcopied_data = copy.deepcopy(data)

    xarray_saver = XarraySaver(merge_arrays=False, file_format="nc")
    processed_data = xarray_saver.process(data)

    assert dicts_equal(data, deepcopied_data)
    assert not dicts_equal(processed_data, data)
