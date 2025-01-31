import inspect
import logging
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from qm.octave.octave_manager import _add_calibration_entries_to_config
from qm.octave.octave_mixer_calibration import MixerCalibrationResults
from qm.type_hinting.general import Number
from qualang_tools.units import unit

logger = logging.getLogger(__name__)


def get_integration_length():
    # Get the source code of the function
    source_code = inspect.getsource(_add_calibration_entries_to_config)
    # Find the line where integration_length is defined
    for line in source_code.split("\n"):
        if "integration_length" in line:
            # Extract the value of integration_length
            integration_length = int(line.split("=")[1].strip())
            return integration_length
    return None


integration_length = get_integration_length()


class CalibrationResultPlotter:
    colors = ["black", "midnightblue", "navy", "darkblue", "mediumblue", "dodgerblue", "white", "lightgrey"]
    custom_cmap = LinearSegmentedColormap.from_list("custom_diverging", colors, N=256)
    u = unit(coerce_to_integer=True)

    def __init__(self, data: MixerCalibrationResults):
        self.data = data
        output_gain = list(self.data.keys())[0][1]
        self.lo_frequency = list(self.data.keys())[0][0]
        self.if_data = data[(self.lo_frequency, output_gain)].image
        self.lo_data = data[(self.lo_frequency, output_gain)]
        self.if_frequency = list(self.if_data.keys())[0]

    @staticmethod
    def _handle_zero_indices_and_masking(data):
        zero_idxs = np.where(data == 0.0)
        zero_list = list(zip(zero_idxs[0], zero_idxs[1]))

        mask = data == 0.0
        data[mask] = np.nan

        return zero_list

    @staticmethod
    def _plot_scan(scan_x, scan_y, data_dbm, zero_list, width, height, xlabel, ylabel):
        plt.pcolor(scan_x, scan_y, data_dbm, cmap=CalibrationResultPlotter.custom_cmap)
        plt.colorbar(label="Power [dBm]")
        ax = plt.gca()
        for ii, _ in enumerate(zero_list):
            rect = Rectangle(
                (scan_x[0][zero_list[ii][1]] - width / 2, scan_y[zero_list[ii][0]][0] - height / 2),
                width,
                height,
                facecolor="black",
                edgecolor="none",
            )
            ax.add_patch(rect)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.axis("equal")

    @staticmethod
    def _convert_to_dbm(volts):
        return 10 * np.log10(volts / (50 * 2) * 1000)

    def show_lo_result(
        self,
    ) -> None:
        """
        Show the result of LO leakage automatic calibration.
        """

        plt.figure(figsize=(11, 8.9))

        plt.subplot(222)

        d = self.lo_data.debug.coarse[0]

        q_scan = d.q_scan * 1000  # convert to mV
        i_scan = d.i_scan * 1000
        zero_list = self._handle_zero_indices_and_masking(d.lo)

        lo = self.u.demod2volts(d.lo, 10_000)
        lo_dbm = self._convert_to_dbm(lo)
        dq = np.mean(np.diff(q_scan, axis=1))
        di = np.mean(np.diff(i_scan, axis=0))

        width = q_scan[0][1] - q_scan[0][0]
        height = i_scan[1][0] - i_scan[0][0]

        self._plot_scan(q_scan, i_scan, lo_dbm, zero_list, width, height, "Q_dc (mV)", "I_dc (mV)")

        plt.text(
            np.min(q_scan) + 0.5 * dq,
            np.max(i_scan) - 0.5 * di,
            f"coarse scan\nLO = {self.lo_frequency / 1e9:.3f}GHz",
            color="k",
            bbox=dict(facecolor="w", alpha=0.8),
            verticalalignment="top",
        )

        if d.fit is None:
            return

        x0, y0 = d.fit.x_min * 1000, d.fit.y_min * 1000

        r = (
            np.min(
                [
                    y0 - np.min(i_scan),
                    np.max(i_scan) - y0,
                    x0 - np.min(q_scan),
                    np.max(q_scan) - x0,
                ]
            )
            * 0.9
        )
        ais = np.linspace(0, 1, 361) * 2 * np.pi
        P = np.array([np.cos(ais), np.sin(ais)]) * r

        O = np.zeros_like(P)
        O[0] += x0
        O[1] += y0

        plt.plot(*(P + O), "k:", linewidth=0.5)

        r1, r2 = d.fit.pol_[3] ** -0.5, d.fit.pol_[5] ** -0.5
        r1, r2 = r1 / np.sqrt(r1 * r2), r2 / np.sqrt(r1 * r2)

        tc = np.cos(d.fit.theta)
        ts = np.sin(d.fit.theta)

        P = np.array([[r1, 0], [0, r2]]) @ P
        P = np.array([[tc, ts], [-ts, tc]]) @ P

        plt.plot(*(P + O), "k--", linewidth=0.5)
        plt.text(
            np.min(q_scan) + 0.5 * dq,
            np.min(i_scan) + 0.5 * di,
            f"DC phase={d.corrections.dc_phase:.5f}\nDC gain={d.corrections.dc_gain:.5f}",
            color="#ff7f0e",
            verticalalignment="bottom",
            horizontalalignment="left",
        )

        plt.plot(x0, y0, "yo", markersize=8)
        plt.plot(x0, y0, "ro", markersize=4)

        plt.text(
            x0,
            y0 - di * 2,
            f"Q_dc={x0:.2f}mV\nI_dc={y0:.2f}mV",
            color="y",
            horizontalalignment="center",
            verticalalignment="top",
        )

        fine_debug_data = self.lo_data.debug.fine

        x0_ref, y0_ref = x0, y0

        d = fine_debug_data[0]

        x0_fine = d.fit.x_min * 1000 + x0_ref
        y0_fine = d.fit.y_min * 1000 + y0_ref

        plt.plot(x0_fine, y0_fine, "wo", markersize=1)

        fine_scale = np.max(d.i_scan) * 1000

        plt.plot(
            x0_ref + np.array([1, 1, -1, -1, 1]) * fine_scale,
            y0_ref + np.array([1, -1, -1, 1, 1]) * fine_scale,
            "w-.",
            linewidth=0.5,
        )

        plt.subplot(224)

        fine_q_scan = d.q_scan * 1000 + x0_ref
        fine_i_scan = d.i_scan * 1000 + y0_ref
        dq = np.mean(np.diff(fine_q_scan, axis=1))
        di = np.mean(np.diff(fine_i_scan, axis=0))

        zero_list = self._handle_zero_indices_and_masking(d.lo)

        lo = self.u.demod2volts(d.lo, 10_000)
        lo_dbm = self._convert_to_dbm(lo)

        width = q_scan[0][1] - q_scan[0][0]
        height = i_scan[1][0] - i_scan[0][0]

        self._plot_scan(fine_q_scan, fine_i_scan, lo_dbm, zero_list, width, height, "Q_dc (mV)", "I_dc (mV)")

        x0, y0 = d.fit.x_min * 1000 + x0_ref, d.fit.y_min * 1000 + y0_ref

        r = (
            np.min(
                [
                    y0 - np.min(fine_i_scan),
                    np.max(fine_i_scan) - y0,
                    x0 - np.min(fine_q_scan),
                    np.max(fine_q_scan) - x0,
                ]
            )
            * 0.9
        )
        ais = np.linspace(0, 1, 361) * 2 * np.pi
        P = np.array([np.cos(ais), np.sin(ais)]) * r

        O = np.zeros_like(P)
        O[0] += x0
        O[1] += y0

        plt.plot(*(P + O), "k:", linewidth=0.5)

        r1, r2 = d.fit.pol_[3] ** -0.5, d.fit.pol_[5] ** -0.5
        r1, r2 = r1 / np.sqrt(r1 * r2), r2 / np.sqrt(r1 * r2)

        tc = np.cos(d.fit.theta)
        ts = np.sin(d.fit.theta)

        P = np.array([[r1, 0], [0, r2]]) @ P
        P = np.array([[tc, ts], [-ts, tc]]) @ P

        plt.plot(*(P + O), "k--", linewidth=0.5)

        plt.text(
            np.min(fine_q_scan) + 0.5 * dq,
            np.min(fine_i_scan) + 0.5 * di,
            f"DC phase={d.corrections.dc_phase:.5f}\nDC gain={d.corrections.dc_gain:.5f}",
            color="#ff7f0e",
            verticalalignment="bottom",
            horizontalalignment="left",
        )

        plt.plot(x0, y0, "yo", markersize=8)
        plt.plot(x0, y0, "ro", markersize=4)

        t = plt.text(
            np.min(fine_q_scan) + 0.5 * dq,
            np.max(fine_i_scan) - 0.5 * di,
            f"fine scan\nLO = {self.lo_frequency / 1e9:.3f}GHz",
            color="k",
            verticalalignment="top",
        )
        t.set_bbox(dict(facecolor="w", alpha=0.8))

        plt.text(
            x0,
            y0 - di * 2,
            f"Q_dc={x0:.2f}mV\nI_dc={y0:.2f}mV",
            color="y",
            horizontalalignment="center",
            verticalalignment="top",
        )

        plt.subplot(223)

        X, Y = d.q_scan, d.i_scan
        p = d.fit.pol

        iq_error = self.u.demod2volts(
            p[0] + p[1] * X + p[2] * Y + p[3] * X**2 + p[4] * X * Y + p[5] * Y**2 - d.lo, 10_000
        )
        iq_error_dbm = self._convert_to_dbm(np.abs(iq_error))

        plt.pcolor(
            fine_q_scan,
            fine_i_scan,
            iq_error_dbm,
            cmap=CalibrationResultPlotter.custom_cmap,
        )
        plt.xlabel("Q (mV)")
        plt.ylabel("I (mV)")
        plt.axis("equal")

        t = plt.text(
            np.min(fine_q_scan) + 0.5 * dq,
            np.max(fine_i_scan) - 1.5 * di,
            "fit error",
            color="k",
        )
        t.set_bbox(dict(facecolor="w", alpha=0.8))

        plt.colorbar(label="Power [dBm]")

        plt.subplot(221)

        plt.xlim(0, 1)
        plt.ylim(0, 1)

        content = [
            "Current result:",
            f"      I_dc = {y0:.02f}mV, Q_dc = {x0:.2f}mV",
            "\nAchieved LO supression:",
            f"{self._get_lo_suppression():.3f} dB",
        ]

        plt.text(
            0.05,
            0.75,
            "\n".join(content),
            horizontalalignment="left",
            verticalalignment="top",
            bbox=dict(facecolor="none", edgecolor="black", boxstyle="round,pad=1"),
        )
        plt.box(False)
        plt.xticks([])
        plt.yticks([])
        plt.suptitle(f"LO auto calibration @ {self.lo_frequency/1e9:.3f}GHz")
        plt.tight_layout()

    def show_if_result(
        self,
    ) -> None:
        """
        Show the result of image sideband automatic calibration.

        Args:
            lo_frequency (Optional[float]): The LO frequency in Hz. If not provided, the first LO frequency in data is used.
            if_freq (Optional[float]): The IF frequency in Hz. If not provided, the first IF frequency in data is used.
            label (str): A label to be used in the plot title.
        """

        if_freq_data = self.if_data[self.if_frequency]

        plt.figure(figsize=(11, 8.9))

        plt.subplot(222)
        r = if_freq_data.coarse

        dp = np.mean(np.diff(r.p_scan, axis=1))
        dg = np.mean(np.diff(r.g_scan, axis=0))

        zero_list = self._handle_zero_indices_and_masking(r.image)

        im = self.u.demod2volts(r.image, 10_000)
        im_dbm = self._convert_to_dbm(im)

        width = r.p_scan[0][1] - r.p_scan[0][0]
        height = r.g_scan[1][0] - r.g_scan[0][0]

        self._plot_scan(r.p_scan, r.g_scan, im_dbm, zero_list, width, height, "phase (rad)", "gain(%)")

        plt.plot(r.phase, r.gain, "yo", markersize=8)
        plt.plot(r.phase, r.gain, "ro", markersize=4)

        plt.text(
            r.phase,
            r.gain - 2 * dg,
            f"phase={r.phase:.5f}\ngain={r.gain:.5f}",
            color="y",
            horizontalalignment="center",
            verticalalignment="top",
        )

        plt.text(
            np.min(r.p_scan) + 1.5 * dp,
            np.max(r.g_scan - 1.5 * dg),
            f"coarse scan\nLO = {self.lo_frequency/1e9:.3f}GHz\nIF = {self.if_frequency/1e6:.3f}MHz",
            color="k",
            bbox=dict(facecolor="w", alpha=0.8),
            verticalalignment="top",
        )

        r = if_freq_data.fine
        p_min = np.min(r.p_scan)
        p_max = np.max(r.p_scan)

        g_min = np.min(r.g_scan)
        g_max = np.max(r.g_scan)

        plt.plot(
            [p_min, p_max, p_max, p_min, p_min],
            [g_min, g_min, g_max, g_max, g_min],
            "w-.",
            linewidth=0.5,
        )

        plt.subplot(224)

        dp = np.mean(np.diff(r.p_scan, axis=1))
        dg = np.mean(np.diff(r.g_scan, axis=0))

        plt.xlabel("phase (rad)")
        plt.ylabel("gain(%)")
        plt.axis("equal")

        zero_list = self._handle_zero_indices_and_masking(r.image)

        im = self.u.demod2volts(r.image, 10_000)
        im_dbm = self._convert_to_dbm(im)

        width = r.p_scan[0][1] - r.p_scan[0][0]
        height = r.g_scan[1][0] - r.g_scan[0][0]

        self._plot_scan(r.p_scan, r.g_scan, im_dbm, zero_list, width, height, "phase (rad)", "gain(%)")

        plt.contour(r.p_scan, r.g_scan, im_dbm, colors="k", alpha=0.5)
        plt.plot(r.phase, r.gain, "yo", markersize=8)
        plt.plot(r.phase, r.gain, "ro", markersize=4)

        plt.text(
            r.phase,
            r.gain - 2 * dg,
            f"phase={r.phase:.5f}\ngain={r.gain:.5f}",
            color="y",
            horizontalalignment="center",
            verticalalignment="top",
        )

        plt.text(
            np.min(r.p_scan) + 1.5 * dp,
            np.max(r.g_scan - 1.5 * dg),
            f"fine scan\nLO = {self.lo_frequency/1e9:.3f}GHz\nIF = {self.if_frequency/1e6:.3f}MHz",
            color="k",
            bbox=dict(facecolor="w", alpha=0.8),
            verticalalignment="top",
        )

        plt.subplot(223)

        X, Y = r.p_scan, r.g_scan
        p = r.fit.pol

        image = self.u.demod2volts(
            p[0] + p[1] * X + p[2] * Y + p[3] * X**2 + p[4] * X * Y + p[5] * Y**2 - r.image, 10_000
        )
        image_dbm = self._convert_to_dbm(np.abs(image))

        self._plot_scan(r.p_scan, r.g_scan, image_dbm, zero_list, width, height, "phase (rad)", "gain")

        plt.plot(r.phase, r.gain, "yo", markersize=8)
        plt.plot(r.phase, r.gain, "ro", markersize=4)

        # plt.colorbar(label="Power [dBm]")

        plt.text(
            np.min(r.p_scan) + 1.5 * dp,
            np.max(r.g_scan - 1.5 * dg),
            f"fit error\nLO = {self.lo_frequency/1e9:.3f}GHz\nIF = {self.if_frequency/1e6:.3f}MHz",
            color="k",
            bbox=dict(facecolor="w", alpha=0.8),
            verticalalignment="top",
        )

        plt.subplot(221)

        plt.xlim(0, 1)
        plt.ylim(0, 1)

        content = [
            "Calibrated parameters:",
            f"      gain = {r.gain*100:.02f}%, phase = {r.phase*180.0/np.pi:.2f}deg",
            "\nAchieved Image sideband supression:",
            f"{self._get_if_suppression():.3f} dB",
        ]

        plt.text(
            0.05,
            0.75,
            "\n".join(content),
            horizontalalignment="left",
            verticalalignment="top",
            bbox=dict(facecolor="none", edgecolor="black", boxstyle="round,pad=1"),
        )
        plt.box(False)
        plt.xticks([])
        plt.yticks([])
        plt.suptitle(
            f"IMAGE auto calibration: LO = {self.lo_frequency/1e9:.3f}GHz, IF = {self.if_frequency/1e6:.3f}MHz"
        )
        plt.tight_layout()

    def _get_if_suppression(
        self,
        lo_frequency: Optional[float] = None,
        if_freq: Optional[float] = None,
    ):
        """
        Calculate the Image sideband suppression achieved by the automatic calibration.

        If the LO frequency is not given, the first LO frequency in the data is used.
        If the IF frequency is not given, the first IF frequency in the data is used.

        Args:
            lo_frequency (Optional[float]): The LO frequency in Hz. If not provided, the first LO frequency in data is used.
            if_freq (Optional[float]): The IF frequency in Hz. If not provided, the first IF frequency in data is used.

        Returns:
            float: The reduction of Image sideband power before vs after calibration in dB units.
        """

        if_freq_data = self.if_data[self.if_frequency]
        image_fine = if_freq_data.fine.image

        if image_fine.min() > 0.0:
            pass
        else:
            mask = image_fine == 0.0
            image_fine[mask] = np.nan

        image = self.u.demod2volts(image_fine, 10_000)
        image_array_dbm = self._convert_to_dbm(image)
        min_image_dbm = np.nanmin(image_array_dbm)

        pol = if_freq_data.fine.fit.pol
        image_0 = self._paraboloid(0, 0, pol)
        image_0_volts = self.u.demod2volts(image_0, 10_000)
        image_0_dbm = self._convert_to_dbm(image_0_volts)
        return min_image_dbm - image_0_dbm

    def _get_lo_suppression(
        self,
    ):
        """
        Calculate the LO leakage suppression achieved by the automatic calibration.

        If the LO frequency is not given, the first LO frequency in the data is used.
        If the IF frequency is not given, the first IF frequency in the data is used.

        Returns:
            float: The reduction of LO leakage power before vs after calibration in dB units.
        """

        i_coarse = self.lo_data.debug.coarse[0].i_scan
        q_coarse = self.lo_data.debug.coarse[0].q_scan

        lo_coarse = self.lo_data.debug.coarse[0].lo
        lo_fine = self.lo_data.debug.fine[0].lo

        if lo_fine.min() > 0.0:
            pass
        else:
            mask = lo_fine == 0.0
            lo_fine[mask] = np.nan

        lo = self.u.demod2volts(lo_fine, 10_000)
        lo_array_dbm = self._convert_to_dbm(lo)
        min_lo_dbm = np.nanmin(lo_array_dbm)

        id_i = np.argwhere(i_coarse[:, 0] == 0.0)
        id_q = np.argwhere(q_coarse[0, :] == 0.0)
        lo = lo_coarse[id_i, id_q][0][0]
        lo_0 = self.u.demod2volts(lo, 10_000)
        lo_0_dbm = self._convert_to_dbm(lo_0)

        return min_lo_dbm - lo_0_dbm

    @staticmethod
    def _paraboloid(x, y, pol):
        return pol[0] + pol[1] * x + pol[2] * y + pol[3] * x**2 + pol[4] * x * y + pol[5] * y**2
