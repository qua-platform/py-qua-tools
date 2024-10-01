from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Dict, Iterator, Sequence, Callable, Tuple, Generator
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator

import numpy as np
from qm.qua import declare, declare_stream, fixed, if_, save, assign, for_
from qualang_tools.loops import from_array


class ScanMode(ABC):
    @abstractmethod
    def get_idxs(self, x_points: int, y_points: int) -> Tuple[np.ndarray, np.ndarray]:
        pass

    def plot_scan(self, x_points: int, y_points: int):
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

    @abstractmethod
    def scan(self, x_vals: Sequence[float], y_vals: Sequence[float]) -> Iterator[None]:
        yield


class RasterScan(ScanMode):
    def get_idxs(self, x_points: int, y_points: int) -> Tuple[np.ndarray, np.ndarray]:
        x_idxs = np.tile(np.arange(x_points), y_points)
        y_idxs = np.repeat(np.arange(y_points), x_points)
        return x_idxs, y_idxs

    def scan(self, x_vals: Sequence[float], y_vals: Sequence[float]):
        voltages = {"x": declare(fixed), "y": declare(fixed)}

        with for_(*from_array(voltages["y"], y_vals)):  # type: ignore
            with for_(*from_array(voltages["x"], x_vals)):  # type: ignore
                yield voltages


class SpiralScan(ScanMode):
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

    def scan(self, x_vals: Sequence[float], y_vals: Sequence[float]):
        movement_direction = declare(fixed, value=1.0)
        half_spiral_idx = declare(int)
        k = declare(int)
        x = declare(fixed, value=0.0)
        y = declare(fixed, value=0.0)
        voltages = {"x": x, "y": y}

        assert len(x_vals) == len(y_vals), "x_vals and y_vals must have the same length"
        num_half_spirals = len(x_vals) - 1
        x_step = x_vals[1] - x_vals[0]
        y_step = y_vals[1] - y_vals[0]

        with for_(half_spiral_idx, 0, half_spiral_idx < num_half_spirals, half_spiral_idx + 1):  # type: ignore
            # First take one step in the opposite XY direction
            with if_(half_spiral_idx > 0):
                assign(x, x - x_step * movement_direction)
                yield voltages

            with for_(k, 0, k < half_spiral_idx, k + 1):  # type: ignore
                assign(y, y + y_step * movement_direction)
                yield voltages

            with for_(k, 0, k < half_spiral_idx, k + 1):  # type: ignore
                assign(x, x + x_step * movement_direction)
                yield voltages

            assign(movement_direction, -movement_direction)

        assign(x, 0)
        assign(y, 0)
