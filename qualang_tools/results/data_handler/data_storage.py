from abc import ABC, abstractmethod
from typing import *
import json
from pathlib import Path

from matplotlib import pyplot as plt


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


class DataProcessor(ABC):
    @abstractmethod
    def process(self, data):
        pass

    @abstractmethod
    def post_process(self, data_folder: Path):
        pass


class MatplotlibPlotSaver(DataProcessor):
    def __init__(self, file_format="png"):
        self.file_format = file_format

    def process(self, data):
        for key, val in iterate_nested_dict(data):
            if isinstance(val, plt.Figure):
                val.savefig(f"{key}.{self.file_format}")
        return data


def save_data(
    data_folder: Path,
    data,
    metadata=None,
    data_filename="data.json",
    metadata_filename="metadata.json",
    data_processors=(),
):
    """Save data to a folder

    :param data_folder: The folder where the data will be saved
    :param data: The data to be saved
    :param metadata: Metadata to be saved
    :param data_filename: The filename of the data
    :param metadata_filename: The filename of the metadata
    :param data_processors: A list of data processors to be applied to the data
    """
    if isinstance(data_folder, str):
        data_folder = Path(data_folder)

    if not data_folder.exists():
        raise NotADirectoryError(f"Save_data: data_folder {data_folder} does not exist")

    if not isinstance(data, dict):
        raise TypeError("save_data: 'data' must be a dictionary")

    processed_data = data
    for data_processor in data_processors:
        processed_data = data_processor.process(processed_data)

    with (data_folder / data_filename).open("w") as f:
        json.dump(processed_data, f)

    if metadata is not None:
        if not isinstance(metadata, dict):
            raise TypeError("save_data: 'metadata' must be a dictionary")

        with (data_folder / metadata_filename).open("w") as f:
            json.dump(metadata, f)

    for data_processor in data_processors:
        data_processor.post_process(data_folder=data_folder)
