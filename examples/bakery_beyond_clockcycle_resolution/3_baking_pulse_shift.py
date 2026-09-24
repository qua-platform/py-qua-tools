"""
Shift a Gaussian pulse's center within a fixed window, in 100 ps steps.

The previous examples used baking's fine grid to sweep a pulse's *duration*
(``T``, i.e. its end). This example sweeps its *start* instead: a leading
``b.wait(shift, ELEMENT)`` before ``b.play(...)`` delays the pulse by
``shift`` within a fixed total window, shifting the Gaussian's center
(``nu`` in ``gaussian(t, nu, sigma, amp)`` terms) without changing its shape.

The wait and the pulse are both authored on the same sub-ns grid, so baking
interpolates them together as one waveform before resampling to the OPX's
1 ns grid. A 100 ps ``shift`` therefore doesn't just move whole zero
samples around — it changes the actual *amplitude* baked into each 1 ns
sample, sliding the envelope by a fraction of a sample.

Every baked op has the same total length (leading wait + pulse + trailing
wait), so they can be indexed uniformly in the QUA program exactly like the
duration sweep in ``2_baking_fine_time_sweep.py``.
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

# Fixed-length Gaussian that gets slid around inside WINDOW_NS.
PULSE_LEN_NS = 16.0
GAUSS_AMP = 0.0003

# 100 ps baking grid: 10 GS/s → one integer unit is 0.1 ns.
BAKING_SAMPLING_RATE = 1e10
DT_NS = 1e9 / BAKING_SAMPLING_RATE  # 0.1

# Total per-op window: fixed, >= 16 ns, multiple of 4 ns, room for every shift.
# The pulse itself occupies PULSE_LEN_NS + DT_NS of playback time: it's built
# from one more sample than PULSE_LEN_NS/DT_NS (so the last sample lands
# exactly at t=PULSE_LEN_NS), and each sample consumes one tick of playback.
WINDOW_NS = 24
SHIFT_MIN_NS = 0.0
SHIFT_MAX_NS = WINDOW_NS - PULSE_LEN_NS - DT_NS  # 7.9
SHIFT_STEP_NS = DT_NS  # 100 ps

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
# Minimal OPX1000 / MW-FEM config. The "gaussian" pulse op is only a
# placeholder; every real waveform comes from the per-shift bakes below.
# ---------------------------------------------------------------------------
gauss_i_1ns = gaussian_i(GAUSS_AMP, int(PULSE_LEN_NS), sampling_rate=1e9)

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
            "length": int(PULSE_LEN_NS),
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
# Bake one waveform per shift: leading wait (delay) + fixed pulse + trailing
# wait (fills out to the fixed WINDOW_NS), all at the baking sampling rate.
# ---------------------------------------------------------------------------
assert SHIFT_STEP_NS == DT_NS, "Shift step must match the baking time unit."
shift_ns = np.arange(SHIFT_MIN_NS, SHIFT_MAX_NS + SHIFT_STEP_NS / 2.0, SHIFT_STEP_NS)
shift_samples = np.round(shift_ns / DT_NS).astype(int)
assert np.allclose(shift_samples * DT_NS, shift_ns), "Shifts must be integer sample counts."

# +1: samples run t=0..(n-1)*dt_ns, so reaching PULSE_LEN_NS exactly needs n = PULSE_LEN_NS/dt_ns + 1.
n_pulse_hr = int(round(PULSE_LEN_NS / DT_NS)) + 1
window_hr = int(round(WINDOW_NS / DT_NS))
i_wf_hr = gaussian_i(GAUSS_AMP, n_pulse_hr, BAKING_SAMPLING_RATE)
q_wf_hr = [0.0] * n_pulse_hr

baking_list = []
for shift_hr in shift_samples:
    shift_hr = int(shift_hr)
    with baking(config, sampling_rate=BAKING_SAMPLING_RATE, padding_method="none") as b:
        b.add_op("gauss_hr", ELEMENT, [i_wf_hr, q_wf_hr])
        b.wait(shift_hr, ELEMENT)
        b.play("gauss_hr", ELEMENT)
        b.wait(window_hr - shift_hr - n_pulse_hr, ELEMENT)
        assert b.get_current_length(ELEMENT) == window_hr
    baking_list.append(b)

print(
    f"Baked {len(baking_list)} waveforms at {BAKING_SAMPLING_RATE / 1e9:.0f} GS/s "
    f"(1 unit = {DT_NS * 1e3:.0f} ps)."
)
print(
    f"Shift sweep: {shift_ns[0]:g} -> {shift_ns[-1]:g} ns, "
    f"step {SHIFT_STEP_NS * 1e3:.0f} ps, pulse length {PULSE_LEN_NS:g} ns, window {WINDOW_NS} ns."
)
print(f"Each baked operation is {baking_list[0].get_op_length(ELEMENT)} ns on the OPX 1 ns grid.")

# ---------------------------------------------------------------------------
# Plot baked envelopes (what is uploaded to the OPX), with a DAC-check
# (does the DAC-rounded waveform still fit its intended Gaussian?) alongside
# each `show_ns` shift. `nu` is the swept parameter here (the shifted pulse
# center); sigma/amp are fixed invariants. Set DAC_CHECK = False to skip
# it, or loop over all of `shift_ns` for full-sweep coverage.
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)

show_ns = [0.0, 1.0, 2.0, 2.2, 5.5]
zoom_ns = [0.0, 0.1, 0.2, 0.3, 0.5]


for shift in show_ns:
    i = index_of(shift_ns, shift)
    samples_i = np.array(config["waveforms"][f"{ELEMENT}_baked_wf_I_{i}"]["samples"])
    axes[0].plot(
        np.arange(len(samples_i)),
        samples_i,
        marker="o",
        markersize=3,
        label=f"shift={shift_ns[i]:g} ns",
    )
    if DAC_CHECK:
        start_ns = shift_ns[i]
        last_ns = start_ns + (n_pulse_hr - 1) * DT_NS
        start_len = int(np.ceil(start_ns))  # exclude the leading pad
        real_len = int(np.floor(last_ns)) + 1  # exclude the trailing pad
        samples_dac_check = samples_i[start_len:real_len]
        # check_dac's t starts at 0, not start_ns, so shift nu0 to match.
        nu0 = start_ns + (n_pulse_hr - 1) * DT_NS / 2.0 - start_len
        p0 = [nu0, n_pulse_hr * DT_NS / 5.0, GAUSS_AMP]
        check_dac(
            gaussian_model,
            samples_dac_check,
            p0,
            tolerance=0.005,
            label=f"shift={shift_ns[i]:g} ns",
        )

for shift in zoom_ns:
    i = index_of(shift_ns, shift)
    samples_i = np.array(config["waveforms"][f"{ELEMENT}_baked_wf_I_{i}"]["samples"])
    axes[1].plot(
        time_from_center(samples_i),
        samples_i,
        label=f"shift={shift_ns[i]:g} ns",
    )

axes[0].set_xlim(-1, WINDOW_NS + 1)
axes[0].set_title("Baked envelopes sliding within the fixed window")
axes[0].set_xlabel("Time (ns)")
axes[0].set_ylabel("I amplitude (full-scale fraction)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].set_title("Zoom: 100 ps shift steps, aligned on pulse center")
axes[1].set_xlabel("Time from pulse center (ns)")
axes[1].set_ylabel("I amplitude (full-scale fraction)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

fig.suptitle(
    f"Pulse-shift sweep at {BAKING_SAMPLING_RATE / 1e9:.0f} GS/s, "
    "then interpolated back to 1 ns"
)

# ---------------------------------------------------------------------------
# QUA program: play each baked waveform in a Python-indexed sweep
# Bake *before* opening a QuantumMachine — baking edits ``config``.
# ---------------------------------------------------------------------------
with program() as shift_sweep:
    n = declare(int)
    j = declare(int)
    with for_(n, 0, n < N_AVG, n + 1):
        with for_(j, 0, j < len(baking_list), j + 1):
            deterministic_run(baking_list, j, unsafe=True)
            align()
            wait(COOLDOWN_CC)


if RUN_MODE == "bake_only":
    plt.show()
elif RUN_MODE == "compile":
    print(generate_qua_script(shift_sweep, config))
    plt.show()
else:
    qmm = QuantumMachinesManager(host=HOST_IP, cluster_name=CLUSTER_NAME)
    if RUN_MODE == "simulate":
        job = qmm.simulate(
            config,
            shift_sweep,
            SimulationConfig(duration=SIMULATION_DURATION_NS // 4),
        )
        job.wait_until("Done", timeout=120)
        samples = job.get_simulated_samples()
        samples.con1.plot()
        try:
            report = job.get_simulated_waveform_report()
            report.create_plot(samples, plot=True)
        except Exception as exc:
            print(f"Waveform report skipped: {exc}")
        plt.show()
    elif RUN_MODE == "execute":
        qm = qmm.open_qm(config)
        job = qm.execute(shift_sweep)
        job.result_handles.wait_for_all_values()
        print("Program finished on hardware.")
        plt.show()
    else:
        raise ValueError(f"Unknown RUN_MODE: {RUN_MODE!r}")
