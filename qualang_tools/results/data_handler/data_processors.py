from pathlib import Path
from abc import ABC
from typing import Dict, Any, Generator, List, Tuple, Optional

from matplotlib import pyplot as plt

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
    def __init__(self, file_format="png"):
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
