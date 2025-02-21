from qm.jobs.qm_job import QmJob
import xarray as xr
from contextlib import contextmanager
import time
import logging
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


@contextmanager
def timer(label: str):
    t0 = time.perf_counter()
    yield
    print(f"{label} - time taken: {time.perf_counter() - t0:.3f} seconds")


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} - time taken: {time.perf_counter() - t0:.3f} seconds")
        return result

    return wrapper


class XarrayDataFetcher:
    ignore_handles = ["readout", "readout_timestamps"]

    def __init__(self, job: QmJob, axes: Optional[Dict[str, xr.DataArray]] = None):
        self.job = job
        self.axes = axes

        self._started_acquisition: bool = False
        self._finished_acquisition: bool = False
        self._t_start: Optional[float] = None

        self._raw_data: Dict[str, Any] = {}

        self.dataset = self.initialize_dataset()

    @timer_decorator
    def retrieve_latest_data(self):
        logger.debug("Starting to retrieve latest data")
        for data_label in self.job.result_handles.keys():
            if data_label in self.ignore_handles:
                logger.debug(f"Skipping ignored handle: {data_label}")
                continue

            latest_data = self.job.result_handles[data_label].fetch_all()
            self._raw_data[data_label] = latest_data

    def initialize_dataset(self):
        return xr.Dataset(coords=self.axes)

    def update_dataset(self):
        raw_data_arrays = self._get_raw_data_arrays()
        if not raw_data_arrays:
            return self.dataset

        # If no axes were provided, simply add the arrays as they are.
        if self.axes is None:
            self._update_no_axes_data_arrays(raw_data_arrays)
            return self.dataset

        # Ensure all raw arrays have the same shape
        array_shapes = [arr.shape for arr in raw_data_arrays.values()]
        if len(set(array_shapes)) != 1:
            raise ValueError("All arrays must have the same shape")
        array_shape = array_shapes[0]

        dims_order = list(self.axes.keys())
        axes_shape = tuple(self.axes[dim].size for dim in dims_order)

        if axes_shape == array_shape:
            self._update_regular_data_arrays(raw_data_arrays, dims_order)
        elif len(axes_shape) == len(array_shape) + 1 and axes_shape[1:] == array_shape:
            self._update_qubit_data_arrays(raw_data_arrays, dims_order)
        else:
            raise ValueError("Axes and arrays have incompatible shapes")

        return self.dataset

    def _get_raw_data_arrays(self) -> Dict[str, np.ndarray]:
        """Filter and return only the raw data entries that are NumPy arrays."""
        return {key: val for key, val in self._raw_data.items() if isinstance(val, np.ndarray)}

    def _update_no_axes_data_arrays(self, raw_data_arrays: Dict[str, np.ndarray]):
        """
        Update the dataset by simply assigning each raw data array without
        any additional dimensions or coordinates.
        """
        for label, data in raw_data_arrays.items():
            self.dataset[label] = xr.DataArray(data)

    def _update_regular_data_arrays(self, raw_data_arrays: Dict[str, np.ndarray], dims_order: List[str]):
        """
        Update the dataset by directly assigning each raw data array to a new variable.
        The dims_order is taken from the keys of the axes dictionary.
        """
        for label, data in raw_data_arrays.items():
            self.dataset[label] = xr.DataArray(data, dims=dims_order, coords=self.axes)

    def _update_qubit_data_arrays(self, raw_data_arrays: Dict[str, np.ndarray], dims_order: List[str]):
        """
        Group raw data keys matching the pattern {label}{idx} and stack them along a new dimension.
        The first coordinate in dims_order is used as the qubit axis.
        """
        import re

        grouped = {}
        for key, data in raw_data_arrays.items():
            m = re.match(r"([a-zA-Z_]+)(\d+)$", key)
            if m:
                base = m.group(1)
                idx = int(m.group(2))
                grouped.setdefault(base, []).append((idx, data))
            else:
                # If the key does not match the pattern, add it using the axes excluding the first dimension.
                self.dataset[key] = xr.DataArray(
                    data, dims=dims_order[1:], coords={dim: self.axes[dim] for dim in dims_order[1:]}
                )
        # Process each grouped variable by stacking the arrays along the qubit axis.
        for base, items in grouped.items():
            items.sort(key=lambda x: x[0])
            arrays = [item[1] for item in items]
            stacked = np.stack(arrays, axis=0)
            self.dataset[base] = xr.DataArray(stacked, dims=[dims_order[0]] + dims_order[1:], coords=self.axes)

    @timer_decorator
    def is_processing(self):
        """Generator that yields True while results are processing and for one final time after completion.
        Final yield will be False."""
        if not self._started_acquisition:
            self._started_acquisition = True
            self._t_start = time.perf_counter()
            self._finished_acquisition = False
            return True

        is_processing = self.job.result_handles.is_processing()
        if is_processing:
            return True

        if not self._finished_acquisition:
            self._finished_acquisition = True
            return True

        return False
