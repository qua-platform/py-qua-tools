from pathlib import Path

from .helpers import copy_nested_dict, iterate_nested_dict, update_nested_dict
from .data_processor import DataProcessor


class XarraySaver(DataProcessor):
    merge_arrays: bool = False
    merged_array_name: str = "xarrays"
    file_format: str = "hdf5"
    nested_separator: str = "."

    def __init__(self, merge_arrays=None, merged_array_name=None, file_format=None):
        if merge_arrays is not None:
            self.merge_arrays = merge_arrays
        if merged_array_name is not None:
            self.merged_array_name = merged_array_name
        if file_format is not None:
            self.file_format = file_format

        self.data_arrays = {}

    @property
    def file_suffix(self) -> str:
        suffixes = {"nc": ".nc", "netcdf": ".nc", "h5": ".h5", "hdf5": ".h5", "zarr": ".zarr"}
        return suffixes[self.file_format.lower()]

    def process(self, data):
        import xarray as xr

        self.data_arrays = {}
        processed_data = copy_nested_dict(data)

        for keys, val in iterate_nested_dict(data):
            if not isinstance(val, xr.Dataset):
                continue

            path = Path(self.nested_separator.join(keys))
            self.data_arrays[path] = val
            if self.merge_arrays:
                merged_array_name = Path(self.merged_array_name).with_suffix(self.file_suffix)
                update_nested_dict(processed_data, keys, f"./{merged_array_name}#{path}")
            else:
                update_nested_dict(processed_data, keys, f"./{path}{self.file_suffix}")
        return processed_data

    def save_merged_netcdf_arrays(self, path: Path, arrays: dict):
        for array_path, array in self.data_arrays.items():
            try:
                array.to_netcdf(path, mode="a", group=str(array_path))
            except ValueError as e:
                raise ValueError(
                    f"Error saving merged array {path}. You may neet to first run `pip install netcdf4`"
                ) from e

    def post_process(self, data_folder: Path):
        if self.file_suffix not in [".nc", ".h5"]:
            raise NotImplementedError(f"File format {self.file_format} is not supported")

        if self.merge_arrays:
            for path, array in self.data_arrays.items():
                merged_path = data_folder / Path(self.merged_array_name).with_suffix(self.file_suffix)
                try:
                    array.to_netcdf(merged_path, mode="a", group=str(path))
                except ValueError as e:
                    raise ValueError(
                        f"Error saving merged array {merged_path}. You may neet to first run `pip install netcdf4`"
                    ) from e
        else:
            for path, array in self.data_arrays.items():
                array.to_netcdf(data_folder / f"{path}{self.file_suffix}")
