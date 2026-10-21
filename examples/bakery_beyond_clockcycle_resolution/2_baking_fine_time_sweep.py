"""
Sweep the duration of a single Gaussian on one MW-FEM channel with 100 ps steps.

QUA ``wait()``/``play(..., duration=...)`` only resolve to 4 ns. Baking lets
you author on a finer grid by raising ``sampling_rate``: each integer unit
then equals ``1 / sampling_rate`` seconds instead of 1 ns
(``sampling_rate=1e10`` -> 1 unit = 100 ps). Keep durations as integers of
that unit, not floats.

On exit, baking interpolates the waveform back onto the OPX's native 1 ns
grid. A 100 ps duration change survives as a slightly stretched *smooth*
envelope on that grid, trading amplitude resolution for temporal resolution
— this only works for a smooth shape like a Gaussian, not a square pulse.

``padding_method="none"`` forbids extra 0-padding, so every baked length
must already be >= 16 ns and a multiple of 4 ns; this example pads every
sweep point up to the same fixed max length to satisfy that.
"""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from qm import QuantumMachinesManager, SimulationConfig, generate_qua_script
from qm.qua import align, declare, for_, program, wait
from qualang_tools.bakery import baking
from qualang_tools.bakery.bakery import deterministic_run

from _utils import check_dac, gaussian_i, gaussian_model, index_of, time_from_center

# ---------------------------------------------------------------------------
# Hardware / experiment knobs
# ---------------------------------------------------------------------------
CON = "con1"
MW_FEM = 1
MW_PORT = 1
MW_BAND = 2
UPCONVERTER_HZ = 5.0e9
QUBIT_IF_HZ = 0 * 100e6
FULL_SCALE_POWER_DBM = 1
ELEMENT = "qubit"

# Nominal pulse stored in the config (1 sample / ns).
PULSE_LEN_NS = 20
GAUSS_AMP = 0.0001  # fraction of full_scale_power_dbm, in [-1, 1]

# 100 ps baking grid: 10 GS/s → one integer unit is 0.1 ns.
BAKING_SAMPLING_RATE = 1e10
DT_NS = 1e9 / BAKING_SAMPLING_RATE  # 0.1

# Duration sweep of the single Gaussian. Steps must land on integer samples.
DURATION_MIN_NS = 16.0
DURATION_MAX_NS = 24.0
DURATION_STEP_NS = DT_NS  # 100 ps

# Connection (used only for simulate / execute).
HOST_IP = "qop_ip"
CLUSTER_NAME = "cluster_name"

# "bake_only" — bake + plot envelopes, no OPX
# "compile"   — also print the generated QUA script
# "simulate"  — QMM simulation
# "execute"   — run on hardware
RUN_MODE = "bake_only"
DAC_CHECK = True
SIMULATION_DURATION_NS = 20_000
N_AVG = 10
COOLDOWN_CC = 100  # 4 ns clock cycles between shots

# ---------------------------------------------------------------------------
# Minimal OPX1000 / MW-FEM config with a 20 ns Gaussian
# ---------------------------------------------------------------------------


gauss_i_1ns = gaussian_i(GAUSS_AMP, PULSE_LEN_NS, sampling_rate=1e9)

config = {
    "version": 1,
    "controllers": {
        CON: {
            "type": "opx1000",
            "fems": {
                MW_FEM: {
                    "type": "MW",
                    "analog_outputs": {
                        MW_PORT: {
                            "band": MW_BAND,
                            "full_scale_power_dbm": FULL_SCALE_POWER_DBM,
                            "upconverters": {1: {"frequency": UPCONVERTER_HZ}},
                        },
                    },
                    "digital_outputs": {},
                    "analog_inputs": {},
                },
            },
        },
    },
    "elements": {
        ELEMENT: {
            "MWInput": {
                "port": (CON, MW_FEM, MW_PORT),
                "upconverter": 1,
            },
            "intermediate_frequency": QUBIT_IF_HZ,
            "operations": {
                "gaussian": "gaussian_pulse",
            },
        },
    },
    "pulses": {
        "gaussian_pulse": {
            "operation": "control",
            "length": PULSE_LEN_NS,
            "waveforms": {
                "I": "gaussian_wf_i",
                "Q": "zero_wf",
            },
        },
    },
    "waveforms": {
        "gaussian_wf_i": {"type": "arbitrary", "samples": gauss_i_1ns},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
}

# ---------------------------------------------------------------------------
# Bake one waveform per duration
# ---------------------------------------------------------------------------
# add_op samples must be given at the baking sampling rate (here 10 GS/s).
# A 20.0 ns pulse is 200 samples; 20.1 ns is 201 samples.
# Pad with wait so every bake has the same high-rate length:
#   DURATION_MAX_NS / DT_NS samples → DURATION_MAX_NS after interpolation.
# That length must be >= 16 ns and a multiple of 4 ns for padding_method="none".

assert DURATION_STEP_NS == DT_NS, "Duration step must match the baking time unit."
duration_ns = np.arange(DURATION_MIN_NS, DURATION_MAX_NS + DURATION_STEP_NS / 2.0, DURATION_STEP_NS)
# +1: samples run t=0..(n-1)*dt_ns, so reaching tau exactly needs n = tau/dt_ns + 1.
duration_samples = np.round(duration_ns / DT_NS).astype(int) + 1
assert np.allclose((duration_samples - 1) * DT_NS, duration_ns), "Durations must be integer sample counts."
max_samples = int(duration_samples[-1])

baked_len_ns = int(max_samples * DT_NS)
if baked_len_ns < 16 or baked_len_ns % 4 != 0:
    raise ValueError(
        f"Baked length after 1 ns interpolation would be {baked_len_ns} ns; "
        "padding_method='none' requires >= 16 ns and a multiple of 4 ns. "
        "Change DURATION_MAX_NS."
    )

baking_list = []
for n_samples in duration_samples:
    n_samples = int(n_samples)
    i_wf = gaussian_i(GAUSS_AMP, n_samples, BAKING_SAMPLING_RATE)
    q_wf = [0.0] * n_samples
    with baking(config, sampling_rate=BAKING_SAMPLING_RATE, padding_method="none") as b:
        # Durations are integers. At 10 GS/s, 1 == 100 ps.
        b.add_op("gauss_hr", ELEMENT, [i_wf, q_wf])
        b.play("gauss_hr", ELEMENT)
        b.wait(max_samples - n_samples, ELEMENT)
        assert b.get_current_length(ELEMENT) == max_samples
    baking_list.append(b)

print(
    f"Baked {len(baking_list)} waveforms at {BAKING_SAMPLING_RATE / 1e9:.0f} GS/s "
    f"(1 unit = {DT_NS * 1e3:.0f} ps)."
)
print(
    f"Duration sweep: {duration_ns[0]:g} -> {duration_ns[-1]:g} ns, "
    f"step {DURATION_STEP_NS * 1e3:.0f} ps."
)
print(f"Each baked operation is {baking_list[0].get_op_length(ELEMENT)} ns on the OPX 1 ns grid.")

def _rms_width_ns(samples: list[float]) -> float:
    """Amplitude-weighted RMS width of the baked envelope, in ns."""
    y = np.abs(np.asarray(samples, dtype=float))
    t = np.arange(len(y), dtype=float)
    weights = y
    total = np.sum(weights)
    if total == 0:
        return float("nan")
    mean = np.sum(t * weights) / total
    var = np.sum(weights * (t - mean) ** 2) / total
    return float(np.sqrt(var))


# Show the 100 ps neighbourhood around the 20 ns config pulse.
print("")
print("Duration (authored)   RMS width on 1 ns grid")
for i, tau in enumerate(duration_ns):
    near_nominal = abs(tau - PULSE_LEN_NS) <= 0.55
    is_edge = np.isclose(tau, DURATION_MIN_NS) or np.isclose(tau, DURATION_MAX_NS)
    if not (near_nominal or is_edge):
        continue
    wf = config["waveforms"][f"{ELEMENT}_baked_wf_I_{i}"]["samples"]
    print(f"  {tau:7.1f} ns            {_rms_width_ns(wf):6.3f} ns")

# ---------------------------------------------------------------------------
# Plot baked envelopes (what is uploaded to the OPX), with a DAC-check
# (does the DAC-rounded waveform still fit its intended Gaussian?) alongside
# each `show_ns` point. Set DAC_CHECK = False to skip it, or loop over all of
# `duration_ns` yourself for full-sweep coverage instead of just `show_ns`.
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)

show_ns = [16.0, 20.0, 20.1, 20.2, 20.4, 20.6, 20.8, 21]
zoom_ns = [20.0, 20.1, 20.2, 20.4, 20.6, 20.8, 21]

for tau in show_ns:
    i = index_of(duration_ns, tau)
    samples_i = np.array(config["waveforms"][f"{ELEMENT}_baked_wf_I_{i}"]["samples"])
    axes[0].plot(
        time_from_center(samples_i, snap_to_1ns=True),
        samples_i,
        marker="o",
        markersize=4,
        label=f"{duration_ns[i]:g} ns",
    )
    if DAC_CHECK:
        n_samp = int(duration_samples[i])
        last_ns = (n_samp - 1) * DT_NS  # true pulse end, matching gaussian_i
        real_len = int(np.floor(last_ns)) + 1  # exclude the trailing pad
        p0 = [last_ns / 2.0, n_samp * DT_NS / 5.0, GAUSS_AMP]  # intended nu, sigma, amp
        samples_dac_check = samples_i[:real_len]
        check_dac(
            gaussian_model,
            samples_dac_check,
            p0,
            tolerance=0.005,
            label=f"{tau:g} ns",
        )

for tau in zoom_ns:
    i = index_of(duration_ns, tau)
    samples_i = np.array(config["waveforms"][f"{ELEMENT}_baked_wf_I_{i}"]["samples"])
    axes[1].plot(time_from_center(samples_i), samples_i, label=f"{duration_ns[i]:g} ns")

half_span_full = 0.5 * max(show_ns) + 2.0
axes[0].set_xlim(-half_span_full, half_span_full)
axes[0].set_title("Baked envelopes on the 1 ns OPX sample grid")
axes[0].set_xlabel("Time from nearest 1 ns sample to peak (ns)")
axes[0].set_ylabel("I amplitude (full-scale fraction)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].set_xticks(np.arange(-np.floor(half_span_full), np.floor(half_span_full) + 1, 2))

half_span = 0.5 * max(zoom_ns) + 2.0
axes[1].set_xlim(-half_span, half_span)
axes[1].set_title("Zoom: 100 ps duration steps, aligned on pulse center")
axes[1].set_xlabel("Time from pulse center (ns)")
axes[1].set_ylabel("I amplitude (full-scale fraction)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

fig.suptitle(
    f"Single-pulse duration sweep at {BAKING_SAMPLING_RATE / 1e9:.0f} GS/s, "
    "then interpolated back to 1 ns"
)

# ---------------------------------------------------------------------------
# QUA program: play each baked waveform in a Python-indexed sweep
# Bake *before* opening a QuantumMachine — baking edits ``config``.
# ---------------------------------------------------------------------------
with program() as duration_sweep:
    n = declare(int)
    j = declare(int)
    with for_(n, 0, n < N_AVG, n + 1):
        with for_(j, 0, j < len(baking_list), j + 1):
            deterministic_run(baking_list, j, unsafe=True)


if RUN_MODE == "bake_only":
    plt.show()
elif RUN_MODE == "compile":
    print(generate_qua_script(duration_sweep, config))
    plt.show()
else:
    qmm = QuantumMachinesManager(host=HOST_IP, cluster_name=CLUSTER_NAME)
    if RUN_MODE == "simulate":
        job = qmm.simulate(
            config,
            duration_sweep,
            SimulationConfig(duration=SIMULATION_DURATION_NS // 4),
        )
        job.wait_until("Done", timeout=120)
        samples = job.get_simulated_samples()
        samples.con1.plot()
        report = job.get_simulated_waveform_report()
        report.create_plot(samples, plot=True)
        print(
            "Note: the simulator and the OPX both play the baked 1 ns waveform. "
            "A 100 ps authored duration change appears as a stretched Gaussian "
            "envelope, not as an extra 1 ns sample."
        )
        plt.show()
    elif RUN_MODE == "execute":
        qm = qmm.open_qm(config)
        job = qm.execute(duration_sweep)
        job.result_handles.wait_for_all_values()
        print("Program finished on hardware.")
        plt.show()
    else:
        raise ValueError(f"Unknown RUN_MODE: {RUN_MODE!r}")
