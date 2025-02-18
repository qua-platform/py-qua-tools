import inspect
import logging
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from qm.octave.octave_manager import _add_calibration_entries_to_config
from qm.octave.octave_mixer_calibration import MixerCalibrationResults
from qualang_tools.units import unit

logger = logging.getLogger(__name__)


class CalibrationResultPlotter:
    colors = ["black", "midnightblue", "navy", "darkblue", "mediumblue", "dodgerblue", "white", "lightgrey"]
    custom_cmap = LinearSegmentedColormap.from_list("custom_diverging", colors, N=256)
    u = unit(coerce_to_integer=True)

    def __init__(self, data: MixerCalibrationResults):
        """
        Initialize the CalibrationResultPlotter with calibration data.

        Args:
            data (MixerCalibrationResults): The mixer calibration results, output of qm.calibrate_element(element).
        """
        first_key = next(iter(data))
        self.lo_frequency = first_key[0]
        self.output_gain = first_key[1]
        self.if_data = data[(self.lo_frequency, self.output_gain)].image
        self.lo_data = data[(self.lo_frequency, self.output_gain)]
        self.if_frequency = next(iter(self.if_data))
        self.integration_length = self._get_integration_length()

    @staticmethod
    def _handle_zero_indices_and_masking(data):
        """
        Handle zero indices and masking for the given data.
        Replaces 0.0 by NaN and returns the indices of zero values.

        Args:
            data (np.ndarray): The data array to process.

        Returns:
            list: A list of tuples containing the indices of zero values.
        """
        zero_idxs = np.where(data == 0.0)
        zero_list = list(zip(zero_idxs[0], zero_idxs[1]))

        mask = data == 0.0
        data[mask] = np.nan

        return zero_list

    @staticmethod
    def _plot_scan(scan_x, scan_y, data_dbm, zero_list, width, height, xlabel, ylabel):
        """
        Plot the scan data.

        Args:
            scan_x (np.ndarray): The x-axis scan data.
            scan_y (np.ndarray): The y-axis scan data.
            data_dbm (np.ndarray): The data in dBm.
            zero_list (list): List of zero value indices.
            width (float): Width of the rectangles to plot.
            height (float): Height of the rectangles to plot.
            xlabel (str): Label for the x-axis.
            ylabel (str): Label for the y-axis.
        """
        plt.pcolor(scan_x, scan_y, data_dbm, cmap=CalibrationResultPlotter.custom_cmap)
        mesh = plt.pcolor(scan_x, scan_y, data_dbm, cmap=CalibrationResultPlotter.custom_cmap)
        mesh.set_array(data_dbm)
        plt.colorbar(mesh, label="Power [dBm]")
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
        """
        Convert voltage to dBm assuming a 50 Ohm impedance.

        Args:
            volts (np.ndarray): The voltage values.

        Returns:
            np.ndarray: The converted dBm values.
        """
        return 10 * np.log10(volts / (50 * 2) * 1000)

    @staticmethod
    def _plot_fit_elliptical_levels(d, x0, y0, q_scan, i_scan):
        """
        Plot the fit elliptical levels.

        Args:
            d: The data containing fit information.
            x0: The x-coordinate of the fit minimum.
            y0: The y-coordinate of the fit minimum.
            q_scan: The 'Q' scan data.
            i_scan: The 'I' scan data.
        """
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

    def show_lo_leakage_calibration_result(self) -> matplotlib.figure.Figure:
        """
        Plots the results of the LO leakage calibration process.

        This method generates a series of subplots that visualize the coarse and fine scans of the LO calibration and
        returns the achieved LO suppression in dB when comparing the power without calibrating the mixers vs
        after calibration. The powers shown correspond to the power seen by the OPX+ inputs when the signal is routed
        internally through the Octave.

        Note: The power at the Octave RF output may vary up to 10dBm.

        Subplots:
        - Top Left: Summary of the current result and achieved LO suppression.
        - Top Right: Coarse scan of Q_dc vs I_dc with LO power in dBm.
        - Bottom Left: Fit error in dBm.
        - Bottom Right: Fine scan of Q_dc vs I_dc with LO power in dBm.

        Returns:
            matplotlib.figure.Figure: The generated figure.
        """

        fig = plt.figure(figsize=(11, 8.9))

        plt.subplot(222)

        d = self.lo_data.debug.coarse[0]  # Get the coarse scan data

        q_scan = d.q_scan * 1000  # convert to mV
        i_scan = d.i_scan * 1000
        zero_list = self._handle_zero_indices_and_masking(
            d.lo
        )  # Get 0.0 indices and mask them with NaN values before converting to dBm

        lo = self.u.demod2volts(d.lo, self.integration_length)
        lo_dbm = self._convert_to_dbm(lo)

        width = q_scan[0][1] - q_scan[0][0]  # Calculate the width and height of the rectangles to plot
        height = i_scan[1][0] - i_scan[0][0]

        self._plot_scan(q_scan, i_scan, lo_dbm, zero_list, width, height, "Q_dc (mV)", "I_dc (mV)")

        plt.text(
            np.min(q_scan) + 0.5 * width,
            np.max(i_scan) - 0.5 * height,
            f"coarse scan\nLO = {self.lo_frequency / 1e9:.3f}GHz",
            color="k",
            bbox=dict(facecolor="w", alpha=0.8),
            verticalalignment="top",
        )

        if d.fit is None:
            raise RuntimeError("Fitting failed!")

        x0, y0 = d.fit.x_min * 1000, d.fit.y_min * 1000  # Convert to mV

        self._plot_fit_elliptical_levels(d, x0, y0, q_scan, i_scan)

        plt.text(
            np.min(q_scan) + 0.5 * width,
            np.min(i_scan) + 0.5 * height,
            f"DC phase={d.corrections.dc_phase:.5f}\nDC gain={d.corrections.dc_gain:.5f}",
            color="#ff7f0e",
            verticalalignment="bottom",
            horizontalalignment="left",
        )

        plt.plot(x0, y0, "yo", markersize=8)
        plt.plot(x0, y0, "ro", markersize=4)

        plt.text(
            x0,
            y0 - height * 2,
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

        zero_list = self._handle_zero_indices_and_masking(d.lo)

        lo = self.u.demod2volts(d.lo, self.integration_length)
        lo_dbm = self._convert_to_dbm(lo)

        width = fine_q_scan[0][1] - fine_q_scan[0][0]
        height = fine_i_scan[1][0] - fine_i_scan[0][0]

        self._plot_scan(fine_q_scan, fine_i_scan, lo_dbm, zero_list, width, height, "Q_dc (mV)", "I_dc (mV)")

        x0, y0 = d.fit.x_min * 1000 + x0_ref, d.fit.y_min * 1000 + y0_ref

        self._plot_fit_elliptical_levels(d, x0, y0, fine_q_scan, fine_i_scan)

        plt.text(
            np.min(fine_q_scan) + 0.5 * width,
            np.min(fine_i_scan) + 0.5 * height,
            f"DC phase={d.corrections.dc_phase:.5f}\nDC gain={d.corrections.dc_gain:.5f}",
            color="#ff7f0e",
            verticalalignment="bottom",
            horizontalalignment="left",
        )

        plt.plot(x0, y0, "yo", markersize=8)
        plt.plot(x0, y0, "ro", markersize=4)

        t = plt.text(
            np.min(fine_q_scan) + 0.5 * width,
            np.max(fine_i_scan) - 0.5 * height,
            f"fine scan\nLO = {self.lo_frequency / 1e9:.3f}GHz",
            color="k",
            verticalalignment="top",
        )
        t.set_bbox(dict(facecolor="w", alpha=0.8))

        plt.text(
            x0,
            y0 - height * 2,
            f"Q_dc={x0:.2f}mV\nI_dc={y0:.2f}mV",
            color="y",
            horizontalalignment="center",
            verticalalignment="top",
        )

        plt.subplot(223)

        X, Y = d.q_scan, d.i_scan
        p = d.fit.pol

        iq_error = self.u.demod2volts(
            p[0] + p[1] * X + p[2] * Y + p[3] * X**2 + p[4] * X * Y + p[5] * Y**2 - d.lo, self.integration_length
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
            np.min(fine_q_scan) + 0.5 * width,
            np.max(fine_i_scan) - 1.5 * height,
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
            f"{self.get_lo_leakage_rejection():.3f} dB",
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
        plt.suptitle(f"LO auto calibration @ {self.lo_frequency / 1e9:.3f}GHz")
        plt.tight_layout()

        return fig

    def show_image_rejection_calibration_result(
        self,
    ) -> matplotlib.figure.Figure:
        """
        Plots the results of the IF image calibration process.

        This method generates a series of subplots that visualize the coarse and fine scans of the IF image calibration
        and returns the achieved image suppression in dB when comparing the power without calibrating the mixers vs
        after calibration. The powers shown correspond to the power seen by the OPX+ inputs when the signal is routed
        internally through the Octave.

        Note: The power at the Octave RF output may vary up to 10dBm.

        Subplots:
        - Top Left: Summary of the current result and achieved image suppression.
        - Top Right: Coarse scan of gain vs phase with image power in dBm.
        - Bottom Left: Fit error in dBm.
        - Bottom Right: Fine scan of gain vs phase with image power in dBm.

        Returns:
            matplotlib.figure.Figure: The generated figure.
        """

        if_freq_data = self.if_data[self.if_frequency]

        fig = plt.figure(figsize=(11, 8.9))

        plt.subplot(222)
        r = if_freq_data.coarse

        zero_list = self._handle_zero_indices_and_masking(r.image)

        im = self.u.demod2volts(r.image, self.integration_length)
        im_dbm = self._convert_to_dbm(im)

        width = r.p_scan[0][1] - r.p_scan[0][0]
        height = r.g_scan[1][0] - r.g_scan[0][0]

        self._plot_scan(r.p_scan, r.g_scan, im_dbm, zero_list, width, height, "phase (rad)", "gain(%)")

        plt.plot(r.phase, r.gain, "yo", markersize=8)
        plt.plot(r.phase, r.gain, "ro", markersize=4)

        plt.text(
            r.phase,
            r.gain - 2 * height,
            f"phase={r.phase:.5f}\ngain={r.gain:.5f}",
            color="y",
            horizontalalignment="center",
            verticalalignment="top",
        )

        plt.text(
            np.min(r.p_scan) + 1.5 * width,
            np.max(r.g_scan - 1.5 * height),
            f"coarse scan\nLO = {self.lo_frequency / 1e9:.3f}GHz\nIF = {self.if_frequency / 1e6:.3f}MHz",
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

        plt.xlabel("phase (rad)")
        plt.ylabel("gain(%)")
        plt.axis("equal")

        zero_list = self._handle_zero_indices_and_masking(r.image)

        im = self.u.demod2volts(r.image, self.integration_length)
        im_dbm = self._convert_to_dbm(im)

        width = r.p_scan[0][1] - r.p_scan[0][0]
        height = r.g_scan[1][0] - r.g_scan[0][0]

        self._plot_scan(r.p_scan, r.g_scan, im_dbm, zero_list, width, height, "phase (rad)", "gain(%)")

        plt.contour(r.p_scan, r.g_scan, im_dbm, colors="k", alpha=0.5)
        plt.plot(r.phase, r.gain, "yo", markersize=8)
        plt.plot(r.phase, r.gain, "ro", markersize=4)

        plt.text(
            r.phase,
            r.gain - 2 * height,
            f"phase={r.phase:.5f}\ngain={r.gain:.5f}",
            color="y",
            horizontalalignment="center",
            verticalalignment="top",
        )

        plt.text(
            np.min(r.p_scan) + 1.5 * width,
            np.max(r.g_scan - 1.5 * height),
            f"fine scan\nLO = {self.lo_frequency / 1e9:.3f}GHz\nIF = {self.if_frequency / 1e6:.3f}MHz",
            color="k",
            bbox=dict(facecolor="w", alpha=0.8),
            verticalalignment="top",
        )

        plt.subplot(223)

        X, Y = r.p_scan, r.g_scan
        p = r.fit.pol

        image = self.u.demod2volts(
            p[0] + p[1] * X + p[2] * Y + p[3] * X**2 + p[4] * X * Y + p[5] * Y**2 - r.image, self.integration_length
        )
        image_dbm = self._convert_to_dbm(np.abs(image))

        self._plot_scan(r.p_scan, r.g_scan, image_dbm, zero_list, width, height, "phase (rad)", "gain")

        plt.plot(r.phase, r.gain, "yo", markersize=8)
        plt.plot(r.phase, r.gain, "ro", markersize=4)

        # plt.colorbar(label="Power [dBm]")

        plt.text(
            np.min(r.p_scan) + 1.5 * width,
            np.max(r.g_scan - 1.5 * height),
            f"fit error\nLO = {self.lo_frequency / 1e9:.3f}GHz\nIF = {self.if_frequency / 1e6:.3f}MHz",
            color="k",
            bbox=dict(facecolor="w", alpha=0.8),
            verticalalignment="top",
        )

        plt.subplot(221)

        plt.xlim(0, 1)
        plt.ylim(0, 1)

        content = [
            "Calibrated parameters:",
            f"      gain = {r.gain * 100:.02f}%, phase = {r.phase * 180.0 / np.pi:.2f}deg",
            "\nAchieved Image sideband supression:",
            f"{self.get_image_rejection():.3f} dB",
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
            f"IMAGE auto calibration: LO = {self.lo_frequency / 1e9:.3f}GHz, IF = {self.if_frequency / 1e6:.3f}MHz"
        )
        plt.tight_layout()

        return fig

    def get_image_rejection(
        self,
    ):
        """
        Calculate the Image sideband suppression achieved by the automatic calibration.

        Returns:
            float: The reduction of Image sideband power without vs after calibration in dB units.
        """

        if_freq_data = self.if_data[self.if_frequency]
        image_fine = if_freq_data.fine.image

        image = self.u.demod2volts(image_fine, self.integration_length)
        image_array_dbm = self._convert_to_dbm(image)
        min_image_dbm = np.nanmin(image_array_dbm)

        pol = if_freq_data.fine.fit.pol
        image_0 = self._paraboloid(0, 0, pol)
        image_0_volts = self.u.demod2volts(image_0, self.integration_length)
        image_0_dbm = self._convert_to_dbm(image_0_volts)
        return min_image_dbm - image_0_dbm

    def get_lo_leakage_rejection(
        self,
    ):
        """
        Calculate the LO leakage suppression achieved by the automatic calibration.

        Returns:
            float: The reduction of LO leakage power without vs after calibration in dB units.
        """

        i_coarse = self.lo_data.debug.coarse[0].i_scan
        q_coarse = self.lo_data.debug.coarse[0].q_scan

        lo_coarse = self.lo_data.debug.coarse[0].lo
        lo_fine = self.lo_data.debug.fine[0].lo

        lo = self.u.demod2volts(lo_fine, self.integration_length)
        lo_array_dbm = self._convert_to_dbm(lo)
        min_lo_dbm = np.nanmin(lo_array_dbm)

        id_i = np.argwhere(i_coarse[:, 0] == 0.0)
        id_q = np.argwhere(q_coarse[0, :] == 0.0)
        lo = lo_coarse[id_i, id_q][0][0]
        lo_0 = self.u.demod2volts(lo, self.integration_length)
        lo_0_dbm = self._convert_to_dbm(lo_0)

        return min_lo_dbm - lo_0_dbm

    @staticmethod
    def _paraboloid(x, y, pol):
        """
        Calculate the value of a paraboloid function.

        Args:
            x (float): The x-coordinate.
            y (float): The y-coordinate.
            pol (np.ndarray): The polynomial coefficients.

        Returns:
            float: The value of the paraboloid at (x, y).
        """
        return pol[0] + pol[1] * x + pol[2] * y + pol[3] * x**2 + pol[4] * x * y + pol[5] * y**2

    @staticmethod
    def _get_integration_length():
        # Get the source code of the function
        source_code = inspect.getsource(_add_calibration_entries_to_config)
        # Find the line where integration_length is defined
        for line in source_code.split("\n"):
            if "integration_length" in line:
                # Extract the value of integration_length
                integration_length = int(line.split("=")[1].strip())
                return integration_length
        return None
