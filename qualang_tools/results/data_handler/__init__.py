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

from .data_folder_tools import *
from .data_handler import *

__all__ = [*data_folder_tools.__all__, data_processors, DEFAULT_DATA_PROCESSORS, *data_handler.__all__]
