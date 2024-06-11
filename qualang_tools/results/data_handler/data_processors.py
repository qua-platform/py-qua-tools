from pathlib import Path
from abc import ABC
from typing import Dict, Any, Generator, List, Tuple, Optional
from matplotlib import pyplot as plt
import numpy as np

__all__ = ["DEFAULT_DATA_PROCESSORS", "DataProcessor", "MatplotlibPlotSaver", "NumpyArraySaver", "XarraySaver"]


DEFAULT_DATA_PROCESSORS = []


def iterate_nested_dict(
    d: Dict[str, Any], parent_keys: Optional[List[str]] = None
) -> Generator[Tuple[List[str], Any], None, None]:
    """Iterate over a nested dictionary

    :param d: The dictionary to iterate over
    :param parent_keys: The keys of the parent dictionary. Used for recursion

    :return: A generator that yields a tuple of the keys and the value

    """
    if parent_keys is None:
        parent_keys = []
    for k, v in d.items():
        keys = parent_keys + [k]
        yield keys, v
        if isinstance(v, dict):
            yield from iterate_nested_dict(v, parent_keys=keys)


def update_nested_dict(d: dict, keys: List[Any], value: Any) -> None:
    """Update a nested dictionary with a new value

    :param d: The dictionary to update
    :param keys: The keys to the value to update
    :param value: The new value to set
    """
    subdict = d
    for key in keys[:-1]:
        subdict = subdict[key]

    subdict[keys[-1]] = value


def copy_nested_dict(d: dict) -> dict:
    """Copy a nested dictionary, but don't make copies of the values

    This function will copy a nested dictionary, but will not make copies of the values. This is useful if copying the
    values may be an expensive operation (e.g. large arrays).
    If you also want to make copies of the values, use `copy.deepcopy`

    :param d: The dictionary to copy
    :return: A new dictionary with the same structure as `d`, but with the same values
    """
    new_dict = {}
    for key, val in d.items():
        if isinstance(val, dict):
            new_dict[key] = copy_nested_dict(val)
        else:
            new_dict[key] = val
    return new_dict


class DataProcessor(ABC):
    def process(self, data):
        return data

    def post_process(self, data_folder: Path):
        pass


class MatplotlibPlotSaver(DataProcessor):
    file_format: str = "png"
    nested_separator: str = "."

    def __init__(self, file_format=None):
        if file_format is not None:
            self.file_format = file_format
        self.data_figures = {}

    @property
    def file_suffix(self):
        suffix = self.file_format
        if not suffix.startswith("."):
            suffix = "." + suffix
        return suffix

    def process(self, data):
        self.data_figures = {}

        processed_data = copy_nested_dict(data)

        for keys, val in iterate_nested_dict(data):
            if not isinstance(val, plt.Figure):
                continue

            file_end = Path(keys[-1]).with_suffix(self.file_suffix)
            path = Path(self.nested_separator.join(keys[:-1] + [str(file_end)]))

            self.data_figures[path] = val
            update_nested_dict(processed_data, keys, f"./{path}")

        return processed_data

    def post_process(self, data_folder: Path):
        for path, fig in self.data_figures.items():
            fig.savefig(data_folder / path)


DEFAULT_DATA_PROCESSORS.append(MatplotlibPlotSaver)


class NumpyArraySaver(DataProcessor):
    merge_arrays: bool = True
    merged_array_name: str = "arrays.npz"
    nested_separator: str = "."

    def __init__(self, merge_arrays=None, merged_array_name=None):
        if merge_arrays is not None:
            self.merge_arrays = merge_arrays
        if merged_array_name is not None:
            self.merged_array_name = merged_array_name

        self.data_arrays = {}

    def process(self, data):
        self.data_arrays = {}
        processed_data = copy_nested_dict(data)

        for keys, val in iterate_nested_dict(data):
            if not isinstance(val, np.ndarray):
                continue

            path = Path(self.nested_separator.join(keys))
            self.data_arrays[path] = val
            if self.merge_arrays:
                update_nested_dict(processed_data, keys, f"./{self.merged_array_name}#{path}")
            else:
                update_nested_dict(processed_data, keys, f"./{path}.npy")
        return processed_data

    def post_process(self, data_folder: Path):
        if self.merge_arrays:
            arrays = {str(path): arr for path, arr in self.data_arrays.items()}
            if arrays:
                np.savez(data_folder / self.merged_array_name, **arrays)
        else:
            for path, arr in self.data_arrays.items():
                np.save(data_folder / f"{path}.npy", arr)


DEFAULT_DATA_PROCESSORS.append(NumpyArraySaver)


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


try:
    import xarray  # noqa: F401

    DEFAULT_DATA_PROCESSORS.append(XarraySaver)
except ImportError:
    pass
