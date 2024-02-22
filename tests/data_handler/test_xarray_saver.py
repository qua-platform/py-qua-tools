import pytest
import sys
from qualang_tools.results.data_handler.data_processors import XarraySaver


def netcdf4_installed():
    try:
        import netCDF4
    except ImportError:
        return False
    return True


def test_xarray_saver_no_xarrays():
    xarray_saver = XarraySaver()
    data = {"a": 1, "b": 2, "c": 3}
    assert xarray_saver.process(data) == data


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


@pytest.mark.skipif(not netcdf4_installed(), reason="netCDF4 not installed")
def test_xarray_saver_merge_netcdf(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": xr.Dataset()}

    xarray_saver = XarraySaver(merge_arrays=True, file_format="nc")
    processed_data = xarray_saver.process(data.copy())

    assert processed_data == {"a": 1, "b": 2, "c": "./xarrays.nc#c", "d": "./xarrays.nc#d"}

    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "xarrays.nc").exists()

    xr.load_dataset(tmp_path / "xarrays.nc", group="c")
    xr.load_dataset(tmp_path / "xarrays.nc", group="d")


@pytest.mark.skipif(not netcdf4_installed(), reason="netCDF4 not installed")
def test_xarray_saver_merge_hdf5(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": xr.Dataset()}

    xarray_saver = XarraySaver(merge_arrays=True, file_format="h5")
    processed_data = xarray_saver.process(data.copy())

    assert processed_data == {"a": 1, "b": 2, "c": "./xarrays.h5#c", "d": "./xarrays.h5#d"}

    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "xarrays.h5").exists()

    xr.load_dataset(tmp_path / "xarrays.h5", group="c")
    xr.load_dataset(tmp_path / "xarrays.h5", group="d")


def test_xarray_saver_no_merge_netcdf(tmp_path):
    import xarray as xr

    data = {"a": 1, "b": 2, "c": xr.Dataset(), "d": xr.Dataset()}

    xarray_saver = XarraySaver(merge_arrays=False)
    processed_data = xarray_saver.process(data.copy())

    assert processed_data == {"a": 1, "b": 2, "c": "./c.h5", "d": "./d.h5"}

    xarray_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "c.h5").exists()
    assert (tmp_path / "d.h5").exists()

    xr.load_dataset(tmp_path / "c.h5")
    xr.load_dataset(tmp_path / "d.h5")
