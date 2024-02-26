"""Tools for handling data folders."""

from pathlib import Path
from typing import Dict, Union, Optional
import re
from datetime import datetime


__all__ = ["DEFAULT_FOLDER_PATTERN", "extract_data_folder_properties", "get_latest_data_folder", "create_data_folder"]


DEFAULT_FOLDER_PATTERN = "%Y-%m-%d/#{idx}_{name}_%H%M%S"


def _validate_datetime(datetime_str: str, datetime_format: str) -> bool:
    """Validate a datetime string with a given format.

    :param datetime_str: The datetime string to validate.
    :param datetime_format: The format of the datetime string.
    :return: True if the datetime string is valid, False otherwise.
    """
    try:
        datetime.strptime(datetime_str, datetime_format)
    except ValueError:
        return False
    return True


def extract_data_folder_properties(
    data_folder: Path, pattern: str = DEFAULT_FOLDER_PATTERN, root_data_folder: Path = None
) -> Optional[Dict[str, Union[str, int, Path]]]:
    """Extract properties from a data folder.

    :param data_folder: The data folder to extract properties from. Should be an absolute path.
    :param pattern: The pattern to extract the properties from, e.g. "#{idx}_{name}_%H%M%S".
    :param root_data_folder: The root data folder to extract the relative path from.
        If not provided, "relative_path" is not included in the properties.

    :return: A dictionary with the extracted properties.
    Dictionary keys:
        - idx: The index of the data folder.
        - name: The name of the data folder.
        - datetime attributes "year", "month", "day", "hour", "minute", "second".
        - path: The absolute path of the data folder.
        - relative_path: The relative path of the data folder w.r.t the root_data_folder.
    """
    pattern = pattern.replace("{idx}", r"(?P<idx>\d+)")
    pattern = pattern.replace("{name}", r"(?P<name>\w+)")
    pattern = pattern.replace("%Y", r"(?P<year>\d{4})")
    pattern = pattern.replace("%m", r"(?P<month>\d{2})")
    pattern = pattern.replace("%d", r"(?P<day>\d{2})")
    pattern = pattern.replace("%H", r"(?P<hour>\d{2})")
    pattern = pattern.replace("%M", r"(?P<minute>\d{2})")
    pattern = pattern.replace("%S", r"(?P<second>\d{2})")

    data_folder = Path(data_folder)
    if root_data_folder is not None:
        folder_path_str = str(data_folder.relative_to(root_data_folder))
    else:
        folder_path_str = data_folder.name

    folder_path_str = folder_path_str.replace("\\", "/")

    regex_match = re.match(pattern, folder_path_str)
    if regex_match is None:
        return None
    properties = regex_match.groupdict()
    properties = {key: int(value) if value.isdigit() else value for key, value in properties.items()}
    properties["path"] = data_folder
    if root_data_folder is not None:
        properties["relative_path"] = data_folder.relative_to(root_data_folder)
    return properties


def get_latest_data_folder(
    root_data_folder: Path,
    folder_pattern: str = DEFAULT_FOLDER_PATTERN,
    relative_path: Path = Path("."),
    current_folder_pattern: str = None,
) -> Optional[Dict[str, Union[str, int]]]:
    """Get the latest data folder in a given root data folder.

    Typically this is the folder within a date folder with the highest index.

    :param root_data_folder: The root data folder to search for the latest data folder.
    :param folder_pattern: The pattern of the data folder, e.g. "%Y-%m-%d/#{idx}_{name}_%H%M%S".
    :param relative_path: The relative path to the data folder. Used for recursive calls.
    :param current_folder_pattern: The current folder pattern. Used for recursive calls.
    :return: A dictionary with the properties of the latest data folder.
    Dictionary keys:
        - idx: The index of the data folder.
        - name: The name of the data folder.
        - datetime attributes "year", "month", "day", "hour", "minute", "second".
        - path: The absolute path of the data folder.
        - relative_path: The relative path of the data folder w.r.t the root_data_folder.
    """
    if isinstance(root_data_folder, str):
        root_data_folder = Path(root_data_folder)

    if not root_data_folder.exists():
        raise NotADirectoryError(f"Root data folder {root_data_folder} does not exist.")

    if current_folder_pattern is None:
        current_folder_pattern = folder_pattern

    current_folder_pattern, *remaining_folder_pattern = current_folder_pattern.split("/", maxsplit=1)

    folder_path = root_data_folder / relative_path

    if not remaining_folder_pattern:
        if "{idx}" not in current_folder_pattern:
            raise ValueError("The folder pattern must contain '{idx}' at the end.")

        folders = {}
        for f in folder_path.iterdir():
            if not f.is_dir():
                continue
            properties = extract_data_folder_properties(f, folder_pattern, root_data_folder=root_data_folder)
            if properties is None:
                continue

            folders[f] = properties
        if not folders:
            return None

        latest_folder, latest_properties = max(folders.items(), key=lambda f: f[1]["idx"])
        return latest_properties
    elif "{idx}" in current_folder_pattern:
        raise ValueError("The folder pattern must only contain '{idx}' in the last part.")
    else:
        # Filter out elements that aren't folders
        folders = filter(lambda f: f.is_dir(), folder_path.iterdir())
        # Filter folders that match the datetime of the current folder pattern
        folders = filter(lambda f: _validate_datetime(f.name, current_folder_pattern), folders)

        if not folders:
            return None

        # Sort folders by name (either datetime or index)
        sorted_folders = sorted(folders, key=lambda f: f.name, reverse=True)

        # Iterate over the folders, recursively call determine_latest_data_folder_idx
        for folder in sorted_folders:
            sub_folder_properties = get_latest_data_folder(
                root_data_folder,
                folder_pattern=folder_pattern,
                current_folder_pattern=remaining_folder_pattern[0],
                relative_path=relative_path / folder.name,
            )
            if sub_folder_properties is not None:
                return sub_folder_properties
        return None


def create_data_folder(
    root_data_folder: Path,
    name: str,
    idx: Optional[int] = None,
    folder_pattern: str = DEFAULT_FOLDER_PATTERN,
    use_datetime: Optional[datetime] = None,
    create: bool = True,
) -> Dict[str, Union[str, int, Path]]:
    """Create a new data folder in a given root data folder.

    First checks the index of the latest data folder and increments by one.

    :param root_data_folder: The root data folder to create the new data folder in.
    :param name: The name of the new data folder.
    :param idx: The index of the new data folder. If not provided, the index is determined automatically.
    :param folder_pattern: The pattern of the data folder, e.g. "%Y-%m-%d/#{idx}_{name}_%H%M%S".
    :param use_datetime: The datetime to use for the folder name.
    :param create: Whether to create the folder or not.
    """
    if isinstance(root_data_folder, str):
        root_data_folder = Path(root_data_folder)

    if not root_data_folder.exists():
        raise NotADirectoryError(f"Root data folder {root_data_folder} does not exist.")

    if use_datetime is None:
        use_datetime = datetime.now()

    if idx is None:
        # Determine the latest folder index and increment by one
        latest_folder_properties = get_latest_data_folder(root_data_folder, folder_pattern=folder_pattern)

        if latest_folder_properties is None:
            # Create new folder with index 1
            idx = 1
        else:
            idx = latest_folder_properties["idx"] + 1

    relative_folder_name = folder_pattern.format(idx=idx, name=name)
    relative_folder_name = use_datetime.strftime(relative_folder_name)

    data_folder = root_data_folder / relative_folder_name

    if data_folder.exists():
        raise FileExistsError(f"Data folder {data_folder} already exists.")

    if not create:
        return {
            "idx": idx,
            "name": name,
            "path": data_folder,
            "relative_path": data_folder.relative_to(root_data_folder),
            **{attr: getattr(use_datetime, attr) for attr in ["year", "month", "day", "hour", "minute", "second"]},
        }

    data_folder.mkdir(parents=True)

    properties = extract_data_folder_properties(data_folder, folder_pattern, root_data_folder)
    if properties is None:
        raise ValueError(f"Could not extract properties from data folder {data_folder}.")

    return properties
