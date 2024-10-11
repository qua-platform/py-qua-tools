from typing import Tuple, List

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from qualang_tools.wirer.visualizer.layout import INSTRUMENT_FIGURE_DIMENSIONS, instrument_id_mapping


def _key(instrument_id: str, con: int):
    return f"{instrument_id}_{con}"


class InstrumentFigureManager:
    def __init__(self):
        self.figures = {}

    def get_ax(self, con: int, slot: int, instrument_id: str) -> Axes:
        instrument_id = instrument_id_mapping[instrument_id]
        key = _key(instrument_id, con)

        if key not in self.figures:
            if instrument_id == "OPX1000":
                fig, axs = self._make_opx1000_figure()
                self.figures[key] = {i + 1: ax for i, ax in enumerate(axs)}
                fig.suptitle(f"con{con} - {instrument_id} Wiring Diagram", fontweight="bold", fontsize=14)
            elif instrument_id == "OPX+":
                fig = self._make_opx_plus_figure()
                self.figures[key] = fig.axes[0]
                fig.suptitle(f"con{con} - {instrument_id} Wiring Diagram", fontweight="bold", fontsize=14)
            elif instrument_id == "Octave":
                fig = self._make_octave_figure()
                self.figures[key] = fig.axes[0]
                fig.suptitle(f"oct{con} - {instrument_id} Wiring Diagram", fontweight="bold", fontsize=14)
            else:
                raise NotImplementedError()

        return self.figures[key][slot] if slot is not None else self.figures[key]

    @staticmethod
    def _make_opx1000_figure() -> Tuple[Figure, List[Axes]]:
        fig, axs = plt.subplots(
            nrows=1,
            ncols=8,
            figsize=(
                INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["width"] * 2,
                INSTRUMENT_FIGURE_DIMENSIONS["OPX1000"]["height"] * 2,
            ),
        )
        for i, ax in enumerate(axs.flat):
            ax.set_ylim([0.15, 1.15])
            ax.set_xlim([0.15 / 8 * 3, 1.15 / 8 * 3])
            ax.set_facecolor("darkgrey")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_aspect("equal")
        fig.subplots_adjust(wspace=0)

        return fig, axs

    @staticmethod
    def _make_opx_plus_figure() -> Figure:
        fig, ax = plt.subplots(
            1,
            1,
            figsize=(
                INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["width"] * 2,
                INSTRUMENT_FIGURE_DIMENSIONS["OPX+"]["height"] * 2,
            ),
        )
        ax.set_ylim([0.15 / 8 * 3, 1.15 / 8 * 3])
        ax.set_xlim([0.15 * 3, 1.15 * 3])
        ax.set_facecolor("darkgrey")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect("equal")

        return fig

    @classmethod
    def _make_octave_figure(cls) -> Figure:
        return cls._make_opx_plus_figure()
