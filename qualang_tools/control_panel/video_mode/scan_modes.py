from abc import ABC, abstractmethod
from typing import Any, Dict, Sequence, Tuple, Generator
import numpy as np
from matplotlib import figure, axes, pyplot as plt
from matplotlib.ticker import MultipleLocator

from qm.qua import declare, fixed, if_, assign, for_, for_each_, QuaVariableType

from qualang_tools.loops import from_array
from qualang_tools.control_panel.video_mode.dash_tools import BaseDashComponent


class ScanMode(BaseDashComponent, ABC):
    """Abstract base class for scan modes, e.g. raster scan, spiral scan, etc.

    The scan mode is used to generate the scan pattern for the video mode.
    """

    def __init__(self, component_id: str = "scan-mode"):
        super().__init__(component_id=component_id)

    @abstractmethod
    def get_idxs(self, x_points: int, y_points: int) -> Tuple[np.ndarray, np.ndarray]:
        pass

    def plot_scan(self, x_points: int, y_points: int) -> Tuple[figure.Figure, axes.Axes]:
        idxs_x, idxs_y = self.get_idxs(x_points, y_points)

        u = np.diff(idxs_x)
        v = np.diff(idxs_y)
        pos_x = idxs_x[:-1] + u / 2
        pos_y = idxs_y[:-1] + v / 2
        norm = np.sqrt(u**2 + v**2)

        fig, ax = plt.subplots()
        ax.plot(idxs_x, idxs_y, marker="o")
        ax.quiver(pos_x, pos_y, u / norm, v / norm, angles="xy", zorder=5, pivot="mid")

        ax.xaxis.grid(True, which="both")
        ax.xaxis.set_minor_locator(MultipleLocator(abs(np.max(u))))
        ax.yaxis.grid(True, which="both")
        ax.yaxis.set_minor_locator(MultipleLocator(abs(np.max(v))))
        plt.show()

        return fig, ax

    @abstractmethod
    def scan(
        self, x_vals: Sequence[float], y_vals: Sequence[float]
    ) -> Generator[Tuple[QuaVariableType, QuaVariableType], None, None]:
        pass


class RasterScan(ScanMode):
    """Raster scan mode.

    The raster scan mode is a simple scan mode that scans the grid in a raster pattern.
    """

    def get_idxs(self, x_points: int, y_points: int) -> Tuple[np.ndarray, np.ndarray]:
        x_idxs = np.tile(np.arange(x_points), y_points)
        y_idxs = np.repeat(np.arange(y_points), x_points)
        return x_idxs, y_idxs

    def scan(
        self, x_vals: Sequence[float], y_vals: Sequence[float]
    ) -> Generator[Tuple[QuaVariableType, QuaVariableType], None, None]:
        voltages = {"x": declare(fixed), "y": declare(fixed)}

        with for_(*from_array(voltages["y"], y_vals)):  # type: ignore
            with for_(*from_array(voltages["x"], x_vals)):  # type: ignore
                yield voltages["x"], voltages["y"]


class SwitchRasterScan(ScanMode):
    """Switch raster scan mode.

    The switch raster scan mode is a scan mode that scans the grid in a raster pattern,
    but the direction of the scan is switched after each row or column.
    This is useful when the scan length is similar to the bias tee frequency.
    """

    @staticmethod
    def interleave_arr(arr: np.ndarray) -> np.ndarray:
        mid_idx = len(arr) // 2
        if len(arr) % 2:
            interleaved = [arr[mid_idx]]
            arr1 = arr[mid_idx + 1 :]
            arr2 = arr[mid_idx - 1 :: -1]
            interleaved += [elem for pair in zip(arr1, arr2) for elem in pair]
        else:
            arr1 = arr[mid_idx:]
            arr2 = arr[mid_idx - 1 :: -1]
            interleaved = [elem for pair in zip(arr1, arr2) for elem in pair]
        return np.array(interleaved)

    def get_idxs(self, x_points: int, y_points: int) -> Tuple[np.ndarray, np.ndarray]:
        y_idxs = self.interleave_arr(np.arange(y_points))
        x_idxs = np.tile(np.arange(x_points), y_points)
        y_idxs = np.repeat(y_idxs, x_points)
        return x_idxs, y_idxs

    def scan(
        self, x_vals: Sequence[float], y_vals: Sequence[float]
    ) -> Generator[Tuple[QuaVariableType, QuaVariableType], None, None]:
        voltages = {"x": declare(fixed), "y": declare(fixed)}

        with for_each_(voltages["y"], self.interleave_arr(y_vals)):  # type: ignore
            with for_(*from_array(voltages["x"], x_vals)):  # type: ignore
                yield voltages["x"], voltages["y"]


class SpiralScan(ScanMode):
    """Spiral scan mode.

    The spiral scan mode is a scan mode that scans the grid in a spiral pattern.
    """

    def get_idxs(self, x_points: int, y_points: int) -> Tuple[np.ndarray, np.ndarray]:
        assert x_points == y_points, "Spiral only works for square grids"

        num_half_spirals = x_points
        x_idx = x_points // 2
        y_idx = y_points // 2

        idxs_x = [x_idx]
        idxs_y = [y_idx]

        for half_spiral_idx in range(num_half_spirals):
            initial_direction_RL = "L" if half_spiral_idx % 2 else "R"
            direction_UD = "U" if half_spiral_idx % 2 else "D"
            direction_LR = "R" if half_spiral_idx % 2 else "L"

            if half_spiral_idx:
                x_idx += 1 if initial_direction_RL == "R" else -1
                idxs_x.append(x_idx)
                idxs_y.append(y_idx)

            for _ in range(half_spiral_idx):
                y_idx += 1 if direction_UD == "U" else -1
                idxs_x.append(x_idx)
                idxs_y.append(y_idx)

            for _ in range(half_spiral_idx):
                x_idx += 1 if direction_LR == "R" else -1
                idxs_x.append(x_idx)
                idxs_y.append(y_idx)

        return np.array(idxs_x), np.array(idxs_y)

    def scan(
        self, x_vals: Sequence[float], y_vals: Sequence[float]
    ) -> Generator[Tuple[QuaVariableType, QuaVariableType], None, None]:
        movement_direction = declare(fixed)
        half_spiral_idx = declare(int)
        k = declare(int)
        x = declare(fixed)
        y = declare(fixed)
        voltages = {"x": x, "y": y}

        assert len(x_vals) == len(
            y_vals
        ), f"x_vals and y_vals must have the same length ({len(x_vals)} != {len(y_vals)})"
        num_half_spirals = len(x_vals)
        x_step = x_vals[1] - x_vals[0]
        y_step = y_vals[1] - y_vals[0]

        assign(movement_direction, -1.0)
        assign(x, 0.0)
        assign(y, 0.0)
        yield voltages["x"], voltages["y"]

        with for_(half_spiral_idx, 0, half_spiral_idx < num_half_spirals, half_spiral_idx + 1):  # type: ignore
            # First take one step in the opposite XY direction
            with if_(half_spiral_idx > 0):  # type: ignore
                assign(x, x - x_step * movement_direction)  # type: ignore
                yield voltages["x"], voltages["y"]

            with for_(k, 0, k < half_spiral_idx, k + 1):  # type: ignore
                assign(y, y + y_step * movement_direction)  # type: ignore
                yield voltages["x"], voltages["y"]

            with for_(k, 0, k < half_spiral_idx, k + 1):  # type: ignore
                assign(x, x + x_step * movement_direction)  # type: ignore
                yield voltages["x"], voltages["y"]

            assign(movement_direction, -movement_direction)  # type: ignore

        assign(x, 0)
        assign(y, 0)
