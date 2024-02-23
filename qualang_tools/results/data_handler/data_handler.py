from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict, Optional, Sequence, Union

from .data_processors import DEFAULT_DATA_PROCESSORS, DataProcessor
from .data_folder_tools import DEFAULT_FOLDER_PATTERN, create_data_folder


__all__ = ["save_data", "DataHandler"]


def save_data(
    data_folder: Path,
    data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    data_filename: str = "data.json",
    metadata_filename: str = "metadata.json",
    data_processors: Sequence[DataProcessor] = (),
) -> Path:
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

    processed_data = data.copy()
    for data_processor in data_processors:
        processed_data = data_processor.process(processed_data)

    json_data = json.dumps(processed_data, indent=4)
    (data_folder / data_filename).write_text(json_data)

    if metadata is not None:
        if not isinstance(metadata, dict):
            raise TypeError("save_data: 'metadata' must be a dictionary")

        with (data_folder / metadata_filename).open("w") as f:
            json.dump(metadata, f)

    for data_processor in data_processors:
        data_processor.post_process(data_folder=data_folder)

    return data_folder


class DataHandler:
    default_data_processors = DEFAULT_DATA_PROCESSORS
    root_data_folder: Path = None
    folder_pattern: str = DEFAULT_FOLDER_PATTERN
    data_filename: str = "data.json"
    metadata_filename: str = "metadata.json"

    def __init__(
        self,
        name: Optional[str] = None,
        data_processors: Optional[Sequence[DataProcessor]] = None,
        root_data_folder: Optional[Union[str, Path]] = None,
        folder_pattern: Optional[str] = None,
        path: Optional[Path] = None,
    ):
        self.name = name
        if data_processors is not None:
            self.data_processors = data_processors
        else:
            self.data_processors = [
                processor() for processor in self.default_data_processors
            ]

        if root_data_folder is not None:
            self.root_data_folder = root_data_folder
        if folder_pattern is not None:
            self.folder_pattern = folder_pattern

        self.path = path
        self.path_properties = None

    def create_data_folder(
        self,
        name: Optional[str] = None,
        idx: Optional[int] = None,
        use_datetime: Optional[datetime] = None,
        create: bool = True,
    ) -> Dict[str, Union[str, int]]:
        """Create a new data folder in the root data folder"""
        if name is not None:
            self.name = name
        if self.name is None:
            raise ValueError("DataHandler: name must be specified")

        self.path_properties = create_data_folder(
            root_data_folder=self.root_data_folder,
            folder_pattern=self.folder_pattern,
            use_datetime=use_datetime,
            name=self.name,
            idx=idx,
            create=create,
        )
        self.path = self.path_properties["path"]
        return self.path_properties

    def save_data(
        self,
        data,
        name=None,
        metadata=None,
        idx=None,
        use_datetime: Optional[datetime] = None,
    ):
        if name is not None:
            self.name = name
        if self.name is None:
            raise ValueError("DataHandler: name must be specified")
        if self.path is None:
            self.create_data_folder(name=self.name, idx=idx, use_datetime=use_datetime)

        return save_data(
            data_folder=self.path,
            data=data,
            metadata=metadata,
            data_filename=self.data_filename,
            metadata_filename=self.metadata_filename,
            data_processors=self.data_processors,
        )
