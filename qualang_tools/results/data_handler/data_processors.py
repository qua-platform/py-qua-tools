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


def update_nested_dict(d, keys, value):
    subdict = d
    for key in keys[:-1]:
        subdict = subdict[key]

    subdict[keys[-1]] = value


class DataProcessor(ABC):
    def process(self, data):
        return data

    def post_process(self, data_folder: Path):
        pass


class MatplotlibPlotSaver(DataProcessor):
    file_format: str = "png"

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

        for keys, val in iterate_nested_dict(data):
            if isinstance(val, plt.Figure):
                path = Path("/".join(keys)).with_suffix(self.file_suffix)

                self.data_figures[path] = val
                update_nested_dict(data, keys, f"./{path}")

        return data

    def post_process(self, data_folder: Path):
        for path, fig in self.data_figures.items():
            fig.savefig(data_folder / path)


DEFAULT_DATA_PROCESSORS.append(MatplotlibPlotSaver)


class NumpyArraySaver(DataProcessor):
    merge_arrays: bool = True
    merged_array_name: str = "arrays.npz"

    def __init__(self, merge_arrays=None, merged_array_name=None):
        if merge_arrays is not None:
            self.merge_arrays = merge_arrays
        if merged_array_name is not None:
            self.merged_array_name = merged_array_name

        self.data_arrays = {}

    def process(self, data):
        self.data_arrays = {}

        for keys, val in iterate_nested_dict(data):
            if not isinstance(val, np.ndarray):
                continue

            path = Path("/".join(keys))
            self.data_arrays[path] = val
            if self.merge_arrays:
                update_nested_dict(data, keys, f"./{self.merged_array_name}#{path}")
            else:
                update_nested_dict(data, keys, f"./{path.with_suffix('.npy')}")
        return data

    def post_process(self, data_folder: Path):
        if self.merge_arrays:
            arrays = {str(path): arr for path, arr in self.data_arrays.items()}
            np.savez(data_folder / self.merged_array_name, **arrays)
        else:
            for path, arr in self.data_arrays.items():
                np.save(data_folder / path.with_suffix(".npy"), arr)


DEFAULT_DATA_PROCESSORS.append(NumpyArraySaver)


class XarraySaver(DataProcessor):
    merge_arrays: bool = False
    merged_array_name: str = "xarrays"
    file_format: str = "hdf5"

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

        for keys, val in iterate_nested_dict(data):
            if not isinstance(val, xr.Dataset):
                continue

            path = Path("/".join(keys))
            self.data_arrays[path] = val
            if self.merge_arrays:
                merged_array_name = Path(self.merged_array_name).with_suffix(self.file_suffix)
                update_nested_dict(data, keys, f"./{merged_array_name}#{path}")
            else:
                update_nested_dict(data, keys, f"./{path.with_suffix(self.file_suffix)}")
        return data

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
                array.to_netcdf(data_folder / path.with_suffix(self.file_suffix))


DEFAULT_DATA_PROCESSORS.append(XarraySaver)
