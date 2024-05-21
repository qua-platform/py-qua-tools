from . import data_processors

DEFAULT_DATA_PROCESSORS = [
    data_processors.MatplotlibPlotSaver,
    data_processors.NumpyArraySaver,
]

try:
    import xarray  # noqa: F401

    DEFAULT_DATA_PROCESSORS.append(data_processors.XarraySaver)
except ImportError:
    pass

from .data_folder_tools import (  # noqa: E402
    DEFAULT_FOLDER_PATTERN,
    extract_data_folder_properties,
    get_latest_data_folder,
    create_data_folder,
)
from .data_handler import save_data, DataHandler  # noqa: E402
from .data_processors import DataProcessor, MatplotlibPlotSaver, NumpyArraySaver, XarraySaver  # noqa: E402


__all__ = [
    "DEFAULT_FOLDER_PATTERN",
    "extract_data_folder_properties",
    "get_latest_data_folder",
    "create_data_folder",
    "DataProcessor",
    "MatplotlibPlotSaver",
    "NumpyArraySaver",
    "XarraySaver",
    "DEFAULT_DATA_PROCESSORS",
    "save_data",
    "DataHandler",
]
