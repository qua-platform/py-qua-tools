from datetime import datetime
from pathlib import Path
import json
import shutil
from typing import Any, Dict, Optional, Sequence, Union
import warnings

from .data_processors import DEFAULT_DATA_PROCESSORS, DataProcessor
from .data_folder_tools import (
    DEFAULT_FOLDER_PATTERN,
    create_data_folder,
    get_latest_data_folder,
    generate_data_folder_relative_path,
)


__all__ = ["save_data", "DataHandler"]

NODE_FILENAME = "node.json"


def save_data(
    data_folder: Path,
    data: Dict[str, Any],
    node_contents: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    data_filename: str = "data.json",
    data_processors: Sequence[DataProcessor] = (),
) -> Path:
    """Save data to a folder

    The data (assumed to be a dict) is saved as a json file to "{data_folder}/{data_filename}", which typically
    follows the format "%Y-%m-%d/#{idx}_{name}_%H%M%S/data.json".
    Non-serialisable contents in data such as figures and arrays are saved into separate files and the paths are
    referenced from the data dictionary.

    This function also applies a list of data processors to the data before saving it. The data processors are
    applied in the order they are provided.

    This function is used by the DataHandler class to save data to a folder.

    :param data_folder: The folder where the data will be saved
    :param data: The data to be saved
    :param node_contents: The contents of the node file
    :param metadata: Metadata to be saved
    :param data_filename: The filename of the data
    :param data_processors: A list of data processors to be applied to the data
    :return: The path of the saved data folder
    """
    if isinstance(data_folder, str):
        data_folder = Path(data_folder)

    if not data_folder.exists():
        raise NotADirectoryError(f"Save_data: data_folder {data_folder} does not exist")

    if (data_folder / NODE_FILENAME).exists():
        raise FileExistsError(f"Save_data: data_folder {data_folder} already contains data")

    node_contents = node_contents.copy()
    if metadata is not None:
        node_contents.setdefault("metadata", {})
        node_contents["metadata"].update(metadata)
    json_node_contents = json.dumps(node_contents, indent=4)
    (data_folder / NODE_FILENAME).write_text(json_node_contents)

    if not isinstance(data, dict):
        raise TypeError("save_data: 'data' must be a dictionary")

    processed_data = data.copy()
    for data_processor in data_processors:
        processed_data = data_processor.process(processed_data)

    json_data = json.dumps(processed_data, indent=4)
    (data_folder / data_filename).write_text(json_data)

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
    additional_files: Dict[str, str] = {}

    def __init__(
        self,
        name: Optional[str] = None,
        data_processors: Optional[Sequence[DataProcessor]] = None,
        root_data_folder: Optional[Union[str, Path]] = None,
        folder_pattern: Optional[str] = None,
        additional_files: Optional[Dict[str, str]] = None,
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

        self.path = None
        self.path_properties = None

    def generate_node_contents(
        self,
        idx: Optional[int] = None,
        use_datetime: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Check if an empty folder has been created, if so, use the idx and datetime from the folder
        if self.path_properties is not None and idx is None and use_datetime is None:
            if not (self.path / NODE_FILENAME).exists():
                idx = self.path_properties["idx"]
                use_datetime = self.path_properties["created_at"]

        if idx is None:
            latest_folder_properties = get_latest_data_folder(self.root_data_folder, folder_pattern=self.folder_pattern)
            idx = latest_folder_properties["idx"] + 1 if latest_folder_properties is not None else 1
        if use_datetime is None:
            use_datetime = datetime.now().astimezone()

        return {
            "created_at": use_datetime.isoformat(timespec="seconds"),
            "metadata": {"name": self.name, "data_path": relative_folder_name, **metadata},
            "data": self.node_data,  # TODO Add self.node_data
            "id": idx,
            "parents": [idx - 1] if idx > 1 else [],
        }

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
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idx: Optional[int] = None,
        node_contents: Optional[Dict[str, Any]] = None,
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

        if node_contents is None:
            # Generate for a new data folder or use existing node_contents if self.path is set and folder is empty
            node_contents = self.generate_node_contents(idx=idx, use_datetime=use_datetime, metadata=metadata)
        elif use_datetime is not None:
            warnings.warn("DataHandler: use_datetime is ignored when node_contents is provided", UserWarning)
        elif idx is not None and idx != node_contents["id"]:
            warnings.warn("DataHandler: idx is ignored when node_contents is provided", UserWarning)

        idx = node_contents["id"]
        use_datetime = datetime.fromisoformat(node_contents["created_at"])

        # At this point we have determined the idx and datetime to use for the data folder
        # It may be that a folder already exists with the same idx and datetime and is populated.
        # In this case we should raise an error

        # Verify that the data folder has not been created and populated

        if isinstance(self.path, Path) and self.path.exists():
            if (self.path / NODE_FILENAME).exists():
                raise FileExistsError(f"Data folder {self.path} already contains data")
            else:
                # The folder has been created but not populated, so we can use it
                pass
        else:
            self.create_data_folder(name=self.name, idx=idx, use_datetime=use_datetime)

        # Optionally we can consider to move this to `DataHandler.generate_node_contents()`
        node_contents["metadata"]["data_path"] = self.path_properties["relative_path"]

        data_folder = save_data(
            data_folder=self.path,
            data=data,
            data_filename=self.data_filename,
            node_filename=NODE_FILENAME,
            node_contents=node_contents,
            data_processors=self.data_processors,
        )

        for source_name, destination_name in self.additional_files.items():
            if not Path(source_name).exists():
                warnings.warn(
                    f"Additional file {source_name} does not exist, not copying",
                    UserWarning,
                )
                continue

            shutil.copy(source_name, data_folder / destination_name)

        return data_folder
