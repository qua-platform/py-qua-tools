import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List


def get_dir_data(save_dir: Path, script_path: Path) -> Path:
    """
    Make and get directory for saving data/files that current script generates.
    The name of directory will be f"{bsedir_data}/{YYYYMMDD}/{script_name}__{HHMMSS}".

    :param basedir_data: str: Base directory for data to save to.
    :param script_path: str: Abspath of the current script.
    :return: str: Created directory path for saving data.
    """

    if not script_path.is_file():
        raise ValueError("Supply script_path=__file__ or a valid filepath!")

    os.makedirs(save_dir, exist_ok=True)
    if not save_dir.is_dir():
        raise ValueError("Supply a valid directory for save_dir!")

    # datetime in yyyymmdd-hhmmss format
    str_date = datetime.now().strftime("%Y-%m-%d")
    str_time = datetime.now().strftime("%H-%M-%S")

    # get directory name for this result
    dirname = "__".join([script_path.stem, str_time])
    dir_data = save_dir / Path(str_date) / Path(dirname)

    # Combine the parent dir path with data
    return dir_data


def save_files(files: List[Path], dir_data: Path, base_dir: Path) -> None:
    """
    save files for a list of file paths.

    :param files: Union[str, List[str]]: List of file paths or a single file path as a string.
    :param files: Union[str, List[str]]: List of file paths or a single file path as a string.
    """

    qm_log = logging.getLogger("qm")
    qm_log.info(f"saving files to {dir_data}")
    for file_from in files:
        if file_from.is_file():
            file_to = dir_data / file_from.relative_to(base_dir)
            os.makedirs(os.path.dirname(str(file_to)), exist_ok=True)
            shutil.copyfile(str(file_from), str(file_to))
            qm_log.info(f"saved: {str(file_from.relative_to(base_dir))}")
        else:
            qm_log.info(f"not found: {str(file_from.relative_to(base_dir))}")


def save_files_and_get_dir_data(
    base_dir: str = None,
    save_dir: str = None,
    script_path: str = None,
    config_files: List[str] = [
        "configuration.py",
        "configuration_with_octave.py",
        "calibration_db.json",
        "optimal_weights.npz",
    ],
) -> str:
    """
    Save specified files to the specified directory.

    :param base_dir: str: Base directory for data and files storage.
    :param save_dir: str: Directory path where files will be saved.
    :param script_path: str: Path to the current script.
    :param config_files: List[str]: List of configuration-related files to save.
    :return: str: Path to the directory where the files are saved.

    Example usage:
        # Suppose base_dir and save_dir are defined in configuration.py
        #   from pathlib import Path
        #   base_dir = Path().absolute()
        #   save_dir = base_dir / 'QM' / 'Data'

        from configuration import *
        from qualang_tools.results import save_files_and_get_dir_data

        save_data = True
        if save_data:
            dir_data = save_files_and_get_dir_data(
                base_dir=base_dir,
                save_dir=save_dir,
                script_path=__file__,
            )
            # Suppose we want to save I, Q, iterations. 
            np.savez(
                file=dir_data / "data.npz",
                I=I,
                Q=Q,
                iterations=iterations,
            )
            # If a matplotlib figure object is available.
            fig.savefig(dir_data / "data_live.png")
    """

    if script_path is None:
        raise ValueError("Please provide script_path=__file__ or a valid filepath!")

    if base_dir is None or save_dir is None:
        raise ValueError(
            "Please provide a base directory as well as save directory!\n"
            + "Here, the base directory means the parent directory of configuration.py\n"
            + "Add, for example, the following code to configuration.py\n"
            + "from pathlib import Path\n"
            + "base_dir = Path().absolute()\n"
            + "save_dir = base_dir / 'QM' / 'Data'"
        )

    if not isinstance(config_files, list):
        raise TypeError("config_files is supposed to be a list of string")

    # convert the files to Path() objects even if already
    script_path = Path(script_path)
    base_dir = Path(base_dir)
    save_dir = Path(save_dir)
    config_files = [base_dir / Path(cf) for cf in config_files]

    # get the current data directory and get the path
    dir_data = get_dir_data(save_dir, script_path)

    # make the data directory
    os.makedirs(str(dir_data), exist_ok=True)

    # copy the script to the data directory
    files = [script_path] + config_files
    save_files(files, dir_data, base_dir)

    return dir_data
