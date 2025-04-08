from pathlib import Path
from matplotlib.figure import Figure

from .helpers import copy_nested_dict, iterate_nested_dict, update_nested_dict
from .data_processor import DataProcessor


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
            if not isinstance(val, Figure):
                continue

            file_end: Path = Path(keys[-1]).with_suffix(self.file_suffix)
            path = Path(self.nested_separator.join(keys[:-1] + [str(file_end)]))

            self.data_figures[path] = val
            update_nested_dict(processed_data, keys, f"./{path}")

        return processed_data

    def post_process(self, data_folder: Path):
        for path, fig in self.data_figures.items():
            fig.savefig(data_folder / path, bbox_inches="tight")
