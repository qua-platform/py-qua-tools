from pathlib import Path
import numpy as np

from .helpers import copy_nested_dict, iterate_nested_dict, update_nested_dict
from .data_processor import DataProcessor


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
