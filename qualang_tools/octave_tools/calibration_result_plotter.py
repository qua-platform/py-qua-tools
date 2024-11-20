import logging
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from qm.octave.octave_mixer_calibration import MixerCalibrationResults
from qm.type_hinting.general import Number
from qualang_tools.units import unit

logger = logging.getLogger(__name__)

# Define the colors from start (blue), midpoint (white), to end (red)
# colors = ["midnightblue", "royalblue", "lightskyblue", "white", "lightgrey"]
colors = ["black","midnightblue", "navy", "darkblue", "mediumblue", "dodgerblue", "white", "lightgrey"]

# Create the colormap
custom_cmap = LinearSegmentedColormap.from_list("custom_diverging", colors, N=256)

u = unit(coerce_to_integer=True)


def show_lo_result(
    data: MixerCalibrationResults,
    lo_freq: Optional[Number] = None,
    label: str = "",
) -> None:
    if lo_freq is None:
        if len(data) == 1:
            lo_freq = list(data.keys())[0][0]

        else:
            print(f"There is a calibration data for {len(data)} LO frequencies. You must choose one")
            return

    try:
        output_gain = list(data.keys())[0][1]
    except IndexError:
        print("No valid calibration result")
        return

    if (lo_freq, output_gain) not in data:
        print(f"No calibration data for LO frequency = {lo_freq / 1e9:.3f}GHz")
        return

    plt.figure(figsize=(11, 8.9))
    # plt.title(f"LO auto calibration @ {lo_freq/1e9:.3f}GHz")

    lo_data = data[(lo_freq, output_gain)]

    plt.subplot(222)

    d = lo_data.debug.coarse[0]

    q_scan = d.q_scan * 1000
    i_scan = d.i_scan * 1000
    lo = u.demod2volts(d.lo, 10_000)
    lo_dbm = 10 * np.log10(lo / 50 * 1000)

    dq = np.mean(np.diff(q_scan, axis=1))
    di = np.mean(np.diff(i_scan, axis=0))

    plt.pcolor(q_scan, i_scan, lo_dbm, cmap=custom_cmap)
    plt.xlabel("Q_dc (mV)")
    plt.ylabel("I_dc (mV)")
    plt.axis("equal")

    cross = np.array(
        [
            [-1, 1, 0, 0, 5, 5, 5, 5, 0, 0, 1, -1, 0, 0, -5, -5, -5],
            [5, 5, 5, 0, 0, 1, -1, 0, 0, -5, -5, -5, -5, 0, 0, -1, 1],
        ]
    )

    plt.colorbar()

    plt.text(
        np.min(q_scan) + 0.5 * dq,
        np.max(i_scan) - 0.5 * di,
        f"{label}coarse scan\nLO = {lo_freq / 1e9:.3f}GHz",
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

    fine_debug_data = lo_data.debug.fine
    if fine_debug_data is None:
        raise ValueError("No fine debug data, cannot plot.")

    x0_ref, y0_ref = x0, y0

    d = lo_data.debug.fine[0]

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
    lo = u.demod2volts(d.lo, 10_000)
    lo_dbm = 10 * np.log10(lo / 50 * 1000)

    dq = np.mean(np.diff(fine_q_scan, axis=1))
    di = np.mean(np.diff(fine_i_scan, axis=0))

    plt.pcolor(fine_q_scan, fine_i_scan, lo_dbm, cmap=custom_cmap)
    plt.xlabel("Q_dc (mV)")
    plt.ylabel("I_dc (mV)")
    plt.axis("equal")

    if lo_data.debug.prev_result is not None:
        plt.plot(
            lo_data.debug.prev_result[1] * 1000 + cross[0] / 5 * dq,
            lo_data.debug.prev_result[0] * 1000 + cross[1] / 5 * di,
            "--",
            color="#aaaaaa",
            linewidth=0.5,
        )

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
        f"fine scan\nLO = {lo_freq / 1e9:.3f}GHz",
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

    plt.colorbar()

    plt.subplot(223)

    X, Y = d.q_scan, d.i_scan
    p = d.fit.pol

    iq_error = u.demod2volts(p[0] + p[1] * X + p[2] * Y + p[3] * X**2 + p[4] * X * Y + p[5] * Y**2 - d.lo, 10_000)
    iq_error_dbm = 10 * np.log10(np.abs(iq_error) / 50 * 1000)

    plt.pcolor(
        fine_q_scan,
        fine_i_scan,
        iq_error_dbm,
        cmap=custom_cmap,
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

    plt.colorbar()

    plt.subplot(221)

    plt.xlim(0, 1)
    plt.ylim(0, 1)

    content = [
        "Current result:",
        f"      I_dc = {y0:.02f}mV, Q_dc = {x0:.2f}mV",
        "Previous result:",
    ]

    if lo_data.debug.prev_result is not None:
        p_x0 = lo_data.debug.prev_result[1] * 1000
        p_y0 = lo_data.debug.prev_result[0] * 1000

        content.append(f"      I_dc = {p_y0:.02f}mV, Q_dc = {p_x0:.2f}mV")
        content.append("Diff:")
        content.append(f"      I_dc = {p_y0-y0:.02f}mV, Q_dc = {p_x0-x0:.2f}mV")

    else:
        content.append("      - none -")

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
    plt.suptitle(f"LO auto calibration @ {lo_freq/1e9:.3f}GHz")
    plt.tight_layout()


def show_if_result(
    data: MixerCalibrationResults,
    lo_freq: Optional[float] = None,
    if_freq: Optional[float] = None,
    label: str = "",
) -> None:

    if lo_freq is None:
        if len(data) == 1:
            lo_freq = list(data)[0][0]

        else:
            print(f"There is a calibration data for {len(data)} LO frequencies. You must choose one")
            return

    try:
        output_gain = list(data)[0][1]
    except IndexError:
        print("No valid calibration result")
        return

    if (lo_freq, output_gain) not in data:
        print(f"No calibration data for LO frequency = {lo_freq/1e9:.3f}GHz")
        return

    if_data = data[(lo_freq, output_gain)].image

    if len(if_data) == 0:
        print(f"No IF calibration results for LO frequency = {lo_freq/1e9:.3f}GHz")
        return

    if if_freq is None:
        if len(if_data) == 1:
            if_freq = list(if_data.keys())[0]
        else:
            logger.debug(
                f"There is a calibration data for {len(if_data)} IF frequencies for "
                f"LO frequency = {lo_freq/1e9:.3f}GHz. You must choose one"
            )
            return

    if_freq_data = if_data[if_freq]
    plt.figure(figsize=(11, 8.9))

    plt.subplot(222)
    r = if_freq_data.coarse

    dp = np.mean(np.diff(r.p_scan, axis=1))
    dg = np.mean(np.diff(r.g_scan, axis=0))

    image = u.demod2volts(r.image, 10_000)
    image_dbm = 10 * np.log10(image / 50 * 1000)

    plt.pcolor(r.p_scan, r.g_scan, image_dbm, cmap=custom_cmap)
    plt.xlabel("phase (rad)")
    plt.ylabel("gain(%)")
    plt.axis("equal")

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

    plt.colorbar()

    plt.text(
        np.min(r.p_scan) + 1.5 * dp,
        np.max(r.g_scan - 1.5 * dg),
        f"{label}coarse scan\nLO = {lo_freq/1e9:.3f}GHz\nIF = {if_freq/1e6:.3f}MHz",
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

    cross = np.array(
        [
            [-1, 1, 0, 0, 5, 5, 5, 5, 0, 0, 1, -1, 0, 0, -5, -5, -5],
            [5, 5, 5, 0, 0, 1, -1, 0, 0, -5, -5, -5, -5, 0, 0, -1, 1],
        ]
    )

    dp = np.mean(np.diff(r.p_scan, axis=1))
    dg = np.mean(np.diff(r.g_scan, axis=0))

    plt.xlabel("phase (rad)")
    plt.ylabel("gain(%)")
    plt.axis("equal")


    image = u.demod2volts(r.image, 10_000)
    image_dbm = 10 * np.log10(np.abs(image) / 50 * 1000 + 1e-7)

    plt.contour(r.p_scan, r.g_scan, image_dbm, colors="k", alpha=0.5)
    plt.pcolor(r.p_scan, r.g_scan, image_dbm, cmap=custom_cmap)

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

    plt.colorbar()

    plt.text(
        np.min(r.p_scan) + 1.5 * dp,
        np.max(r.g_scan - 1.5 * dg),
        f"{label}fine scan\nLO = {lo_freq/1e9:.3f}GHz\nIF = {if_freq/1e6:.3f}MHz",
        color="k",
        bbox=dict(facecolor="w", alpha=0.8),
        verticalalignment="top",
    )

    if if_freq_data.prev_result is not None:

        p_gain = if_freq_data.prev_result[0]
        p_phase = if_freq_data.prev_result[1]

        plt.plot(
            p_phase + cross[0] / 5 * dp * 2,
            p_gain + cross[1] / 5 * dg * 2,
            "--",
            color="#aaaaaa",
            linewidth=0.5,
        )

    plt.subplot(223)

    X, Y = r.p_scan, r.g_scan
    p = r.fit.pol

    image = u.demod2volts(p[0] + p[1] * X + p[2] * Y + p[3] * X**2 + p[4] * X * Y + p[5] * Y**2 - r.image, 10_000)
    image_dbm = 10 * np.log10(np.abs(image) / 50 * 1000)

    plt.pcolor(r.p_scan, r.g_scan, image_dbm, cmap=custom_cmap)
    plt.xlabel("phase (rad)")
    plt.ylabel("gain")
    plt.axis("equal")

    plt.plot(r.phase, r.gain, "yo", markersize=8)
    plt.plot(r.phase, r.gain, "ro", markersize=4)

    plt.colorbar()

    plt.text(
        np.min(r.p_scan) + 1.5 * dp,
        np.max(r.g_scan - 1.5 * dg),
        f"{label}fit error\nLO = {lo_freq/1e9:.3f}GHz\nIF = {if_freq/1e6:.3f}MHz",
        color="k",
        bbox=dict(facecolor="w", alpha=0.8),
        verticalalignment="top",
    )

    plt.subplot(221)

    plt.xlim(0, 1)
    plt.ylim(0, 1)

    content = [
        "Current result:",
        f"      gain = {r.gain*100:.02f}%, phase = {r.phase*180.0/np.pi:.2f}deg",
        "Previous result:",
    ]

    if if_freq_data.prev_result is not None:

        p_gain = if_freq_data.prev_result[0]
        p_phase = if_freq_data.prev_result[1]

        content.append(f"      gain = {p_gain*100:.02f}%, phase = {p_phase*180.0/np.pi:.2f}deg")
        content.append("Diff:")
        content.append(f"      gain = {(p_gain-r.gain)*100:.02f}%, phase = {(p_phase-r.phase)*180.0/np.pi:.2f}deg")

    else:
        content.append("      - none -")

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
    plt.suptitle(f"IMAGE auto calibration: LO = {lo_freq/1e9:.3f}GHz, IF = {if_freq/1e6:.3f}MHz")
    plt.tight_layout()
