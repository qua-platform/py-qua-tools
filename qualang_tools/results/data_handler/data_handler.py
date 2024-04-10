from datetime import datetime
from pathlib import Path
import json
import shutil
from typing import Any, Dict, Optional, Sequence, Union
import warnings

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
    """
    Save data to a folder

    The data (assumed to be a dict) is saved as a json file to "{data_folder}/{data_filename}", which typically
    follows the format "%Y-%m-%d/#{idx}_{name}_%H%M%S/data.json".
    Non-serialisable contents in data such as figures and arrays are saved into separate files and the paths are
    referenced from the data dictionary.
    The optional metadata (assumed to be a dict) is saved as a json file to "{data_folder}/{metadata_filename}".

    This function also applies a list of data processors to the data before saving it. The data processors are
    applied in the order they are provided.

    This function is used by the DataHandler class to save data to a folder.

    :param data_folder: The folder where the data will be saved
    :param data: The data to be saved
    :param metadata: Metadata to be saved
    :param data_filename: The filename of the data
    :param metadata_filename: The filename of the metadata
    :param data_processors: A list of data processors to be applied to the data
    :return: The path of the saved data folder
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
    """A class to handle data saving.

    This class provides functionality to save data to a specified data folder.
    It allows for the creation of a new data folder, saving data to the folder,
    and applying data processors to the saved data.

    :param name: The name of the data handler.
    :type name: str, optional
    :param data_processors: The data processors to be applied to the saved data.
    :type data_processors: Sequence[DataProcessor], optional
    :param root_data_folder: The root folder where the data will be saved.
    :type root_data_folder: str or Path, optional
    :param folder_pattern: The pattern used to create the data folder.
    :type folder_pattern: str, optional
    :param path: The path to the data folder.
    :type path: Path, optional

    Example usage:

    .. code-block:: python

        data_handler = DataHandler("T1_experiment")
        data = {"T1": 1e-6, "T1_arr": np.array([1, 2, 3]), "T1_fig": plt.figure()}
        data_handler.save_data(data)
    """

    default_data_processors = DEFAULT_DATA_PROCESSORS
    root_data_folder: Path = None
    folder_pattern: str = DEFAULT_FOLDER_PATTERN
    data_filename: str = "data.json"
    metadata_filename: str = "metadata.json"
    additional_files: Dict[str, str] = {}

    def __init__(
        self,
        name: Optional[str] = None,
        data_processors: Optional[Sequence[DataProcessor]] = None,
        root_data_folder: Optional[Union[str, Path]] = None,
        folder_pattern: Optional[str] = None,
        additional_files: Optional[Dict[str, str]] = None,
        path: Optional[Path] = None,
    ):
        self.name = name
        if data_processors is not None:
            self.data_processors = data_processors
        else:
            self.data_processors = [processor() for processor in self.default_data_processors]

        if root_data_folder is not None:
            self.root_data_folder = root_data_folder
        if folder_pattern is not None:
            self.folder_pattern = folder_pattern
        if additional_files is not None:
            self.additional_files = additional_files

        self.path = path
        self.path_properties = None

    def create_data_folder(
        self,
        name: Optional[str] = None,
        idx: Optional[int] = None,
        use_datetime: Optional[datetime] = None,
        create: bool = True,
    ) -> Dict[str, Union[str, int]]:
        """Create a new data folder in the root data folder.

        This method creates a new data folder in the root data folder specified
        in the `root_data_folder` attribute. The name of the data folder can be
        specified using the `name` parameter. An index can also be provided using
        the `idx` parameter. If a datetime object is provided using the `use_datetime`
        parameter, it will be used in the folder name. By default, the data folder
        is created.

        :param name: The name of the data folder.
        :type name: str, optional
        :param idx: The index of the data folder.
        :type idx: int, optional
        :param use_datetime: The datetime to be used in the folder name.
        :type use_datetime: datetime, optional
        :param create: Whether to create the data folder or not.
        :type create: bool, optional
        :return: The properties of the created data folder.
        :rtype: dict
        :raises ValueError: If the name is not specified.

        Example usage:

        .. code-block:: python

            data_handler.create_data_folder(name="T1_experiment", idx=1, use_datetime=datetime.now())
        """
        if name is not None:
            self.name = name
        if self.name is None:
            raise ValueError("DataHandler: name must be specified")
        if self.root_data_folder is None:
            raise ValueError("DataHandler: root_data_folder must be specified")

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
        """Save the data to the data folder.

        This method saves the provided data to the data folder specified in the
        `path` attribute. The name of the data folder can be specified using the
        `name` parameter. The metadata associated with the data can be provided
        using the `metadata` parameter. An index can also be provided using the
        `idx` parameter. If a datetime object is provided using the `use_datetime`
        parameter, it will be used in the folder name.

        A new data folder is created if
        - the `path` attribute is not set
        - the `path` attribute is set and the data folder already contains data

        :param data: The data to be saved.
        :type data: any
        :param name: The name of the data folder.
        :type name: str, optional
        :param metadata: The metadata associated with the data.
        :type metadata: any, optional
        :param idx: The index of the data folder.
        :type idx: int, optional
        :param use_datetime: The datetime to be used in the folder name.
        :type use_datetime: datetime, optional
        :raises ValueError: If the name is not specified.
        :return: The result of saving the data.
        :rtype: any

        Example usage:

        .. code-block:: python

            data_handler.save_data(data, name="T1_experiment", metadata=metadata, idx=1, use_datetime=datetime.now())
        """
        if name is not None:
            self.name = name
        if self.name is None:
            raise ValueError("DataHandler: name must be specified")
        if self.path is None:
            self.create_data_folder(name=self.name, idx=idx, use_datetime=use_datetime)
        elif self.path is not None and (self.path / self.data_filename).exists():
            self.create_data_folder(name=self.name, idx=idx, use_datetime=use_datetime)

        data_folder = save_data(
            data_folder=self.path,
            data=data,
            metadata=metadata,
            data_filename=self.data_filename,
            metadata_filename=self.metadata_filename,
            data_processors=self.data_processors,
        )

        for source_name, destination_name in self.additional_files.items():
            if not Path(source_name).exists():
                warnings.warn(f"Additional file {source_name} does not exist, not copying", UserWarning)
                continue

            shutil.copy(source_name, data_folder / destination_name)

        return data_folder
