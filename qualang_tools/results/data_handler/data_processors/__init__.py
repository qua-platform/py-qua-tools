from typing import List, Type

from .data_processor import DataProcessor
from .matplotlib_plot_saver import MatplotlibPlotSaver
from .numpy_array_saver import NumpyArraySaver
from .xarray_saver import XarraySaver
from .waveform_report_saver import WaveformReportSaver
from .simulator_controller_samples_saver import SimulatorControllerSamplesSaver
from .plotly_graph_saver import PlotlyGraphSaver

DEFAULT_DATA_PROCESSORS: List[Type[DataProcessor]] = [
    DataProcessor,
    WaveformReportSaver,
    SimulatorControllerSamplesSaver,
    MatplotlibPlotSaver,
    NumpyArraySaver,
]

try:
    import xarray  # noqa: F401

    DEFAULT_DATA_PROCESSORS.append(XarraySaver)
except ImportError:
    pass

try:
    import plotly  # noqa: F401

    DEFAULT_DATA_PROCESSORS.append(PlotlyGraphSaver)
except ImportError:
    pass


__all__ = [
    "DataProcessor",
    "MatplotlibPlotSaver",
    "NumpyArraySaver",
    "XarraySaver",
    "WaveformReportSaver",
    "SimulatorControllerSamplesSaver",
    "DEFAULT_DATA_PROCESSORS",
]
