"""
Arbitrarily long Gaussian duration sweep at 100 ps, using baking + waveform cache.

Why not the earlier examples
-----------------------------
* Baking every duration into its own config operation explodes waveform *and*
  program memory (10 000 unique 1 us Gaussians at 100 ps is not practical).
* Hybrid ``play(duration=)`` + baked remainder is exact for *squares*, but
  24 ns of one Gaussian plus 3 ns of another is not a 27 ns Gaussian.

OPX1000 waveform cache
----------------------
Store many equal-length arbitrary waveforms in a ``type: "array"``
``samples_array`` (up to 1024 entries per array, 31 arrays per core, 256 MB).
At runtime ``load_waveform(operation, index, element)`` copies one entry into
the play buffer (non-deterministic duration: keep it *outside* ``strict_timing_``).
The next ``play`` uses that envelope. Unique Gaussians, one pulse in the config.

Baking supplies the sub-ns grid: ``sampling_rate=1e10`` so each integer sample
is 100 ps. On exit, baking interpolates back to 1 ns. Cache entries must all
have the same length, so every Gaussian is right-padded to ``PAD_NS``.

Scale-up
--------
Default sweep is 16-32 ns at 100 ps (fits in one array). For 1 ns -> 1 us at
100 ps set ``DURATION_MAX_NS = 1000``; the example splits into several arrays
of 1024. If even that is too large, precompile once with ``override=True`` and
``qm.queue.add_compiled(..., overrides=b.get_waveforms_dict())`` to swap *one*
overridable waveform per shot (unlimited unique shapes, slower, no inner QUA
duration loop).
"""

from __future__ import annotations

from copy import deepcopy

import numpy as np
from matplotlib import pyplot as plt
from qm import QuantumMachinesManager, SimulationConfig, generate_qua_script
from qm.qua import (
    align,
    assign,
    case_,
    declare,
    for_,
    load_waveform,
    play,
    program,
    strict_timing_,
    switch_,
    wait,
)
from qualang_tools.bakery import baking

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

GAUSS_AMP = 0.0003
BAKING_SAMPLING_RATE = 1e10  # 100 ps per integer sample
DT_NS = 1e9 / BAKING_SAMPLING_RATE

# 16 -> 32 ns at 100 ps = 161 points, one cache array.
# For 1 us at 100 ps: DURATION_MAX_NS = 1000 (multiple arrays of 1024).
DURATION_MIN_NS = 16.0
DURATION_MAX_NS = 32.0
DURATION_STEP_NS = DT_NS

MAX_WF_PER_ARRAY = 1024  # OPX1000 waveform-cache limit per samples_array

HOST_IP = "qop_ip"
CLUSTER_NAME = "cluster_name"

# "bake_only" — build cache + plot, no OPX
# "compile"   — also print the generated QUA script
# "simulate"  — QMM simulation
# "execute"   — run on hardware
RUN_MODE = "bake_only"
DAC_CHECK = True
SIMULATION_DURATION_NS = 20_000
N_AVG = 10
COOLDOWN_CC = 100

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_bake_template() -> dict:
    """Minimal MW-FEM config used only as a baking scratchpad."""
    dummy = gaussian_i(GAUSS_AMP, 16, sampling_rate=1e9)
    return {
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
                "MWInput": {"port": (CON, MW_FEM, MW_PORT), "upconverter": 1},
                "intermediate_frequency": QUBIT_IF_HZ,
                "operations": {"dummy": "dummy_pulse"},
            },
        },
        "pulses": {
            "dummy_pulse": {
                "operation": "control",
                "length": 16,
                "waveforms": {"I": "dummy_i", "Q": "zero_wf"},
            },
        },
        "waveforms": {
            "dummy_i": {"type": "arbitrary", "samples": dummy},
            "zero_wf": {"type": "constant", "sample": 0.0},
        },
        "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
    }


def bake_padded_gaussian(t_ns: float, pad_ns: int) -> list[float]:
    """Gaussian of duration ``t_ns`` on the 100 ps grid, interpolated to 1 ns, right-padded."""
    # +1: samples run t=0..(n-1)*dt_ns, so reaching t_ns exactly needs n = t_ns/dt_ns + 1.
    n_hr = int(round(t_ns / DT_NS)) + 1
    cfg = deepcopy(make_bake_template())
    with baking(cfg, sampling_rate=BAKING_SAMPLING_RATE, padding_method="right") as b:
        i_wf = gaussian_i(GAUSS_AMP, n_hr, BAKING_SAMPLING_RATE)
        b.add_op("g", ELEMENT, [i_wf, [0.0] * n_hr])
        b.play("g", ELEMENT)
    samples = list(cfg["waveforms"][f"{ELEMENT}_baked_wf_I_0"]["samples"])
    if len(samples) > pad_ns:
        raise ValueError(f"Baked length {len(samples)} ns exceeds PAD_NS={pad_ns}.")
    return samples + [0.0] * (pad_ns - len(samples))


# ---------------------------------------------------------------------------
# Duration grid and cache
# ---------------------------------------------------------------------------
assert DURATION_STEP_NS == DT_NS, "Duration step must match the baking time unit."
duration_ns = np.arange(DURATION_MIN_NS, DURATION_MAX_NS + DURATION_STEP_NS / 2.0, DURATION_STEP_NS)
n_points = len(duration_ns)
PAD_NS = int(np.ceil(DURATION_MAX_NS / 4.0) * 4)
if PAD_NS < 16:
    PAD_NS = 16

n_arrays = int(np.ceil(n_points / MAX_WF_PER_ARRAY))
if n_arrays > 31:
    raise ValueError(
        f"Need {n_arrays} waveform arrays; OPX1000 allows 31 per core. "
        "Increase DURATION_STEP_NS or lower DURATION_MAX_NS."
    )

print(
    f"Baking {n_points} Gaussians at {BAKING_SAMPLING_RATE / 1e9:.0f} GS/s "
    f"(1 unit = {DT_NS * 1e3:.0f} ps), padded to {PAD_NS} ns."
)
print(f"Duration sweep: {duration_ns[0]:g} -> {duration_ns[-1]:g} ns.")
print(f"Cache: {n_arrays} samples_array(s) x up to {MAX_WF_PER_ARRAY} waveforms.")

samples_i = [bake_padded_gaussian(float(t), PAD_NS) for t in duration_ns]

chunks_i = [
    samples_i[k * MAX_WF_PER_ARRAY : (k + 1) * MAX_WF_PER_ARRAY] for k in range(n_arrays)
]

config = make_bake_template()
config["elements"][ELEMENT]["operations"] = {}
config["pulses"] = {}
config["waveforms"] = {"zero_wf": {"type": "constant", "sample": 0.0}}

op_names = []
for k, chunk in enumerate(chunks_i):
    op = "gaussian" if n_arrays == 1 else f"gaussian_{k}"
    op_names.append(op)
    wf_i = "gauss_i" if n_arrays == 1 else f"gauss_i_{k}"
    config["waveforms"][wf_i] = {"type": "array", "samples_array": chunk}
    config["pulses"][f"{op}_pulse"] = {
        "operation": "control",
        "length": PAD_NS,
        "waveforms": {"I": wf_i, "Q": "zero_wf"},
    }
    config["elements"][ELEMENT]["operations"][op] = f"{op}_pulse"

# ---------------------------------------------------------------------------
# Plot a few cached envelopes, aligned on the pulse center (integer 1 ns
# grid), with a DAC-check (does the DAC-rounded waveform still fit its
# intended Gaussian?) alongside each `show_ns` point. Set DAC_CHECK = False
# to skip it, or loop over all of `duration_ns` for full-sweep coverage.
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)

show_ns = [16.0, 20.0, 24.0, 28.0, 32.0]
zoom_ns = [20.0, 20.1, 20.2, 20.5, 21.0]
show_ns = [t for t in show_ns if t <= DURATION_MAX_NS + 1e-9]
zoom_ns = [t for t in zoom_ns if DURATION_MIN_NS - 1e-9 <= t <= DURATION_MAX_NS + 1e-9]

for tau in show_ns:
    i = index_of(duration_ns, tau)
    y = np.array(samples_i[i])
    axes[0].plot(time_from_center(y, snap_to_1ns=True), y, marker="o", markersize=3, label=f"{tau:g} ns")
    if DAC_CHECK:
        n_hr = int(round(tau / DT_NS)) + 1
        last_ns = (n_hr - 1) * DT_NS
        real_len = int(np.floor(last_ns)) + 1  # exclude the trailing pad
        p0 = [last_ns / 2.0, n_hr * DT_NS / 5.0, GAUSS_AMP]
        samples_dac_check = samples_i[i][:real_len]
        check_dac(
            gaussian_model,
            samples_dac_check,
            p0,
            tolerance=0.005,
            label=f"{tau:g} ns",
        )

for tau in zoom_ns:
    y = np.array(samples_i[index_of(duration_ns, tau)])
    axes[1].plot(time_from_center(y), y, label=f"{tau:g} ns")

half = 0.5 * DURATION_MAX_NS + 2.0
axes[0].set_xlim(-half, half)
axes[0].set_title("Cached Gaussians on the 1 ns OPX grid")
axes[0].set_xlabel("Time from nearest 1 ns sample to peak (ns)")
axes[0].set_ylabel("I amplitude (full-scale fraction)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].set_xlim(-half, half)
axes[1].set_title("Zoom: 100 ps duration steps (true Gaussians, not concatenated)")
axes[1].set_xlabel("Time from pulse center (ns)")
axes[1].set_ylabel("I amplitude (full-scale fraction)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

fig.suptitle(
    f"Waveform cache: {n_points} baked Gaussians, pad={PAD_NS} ns, "
    f"{BAKING_SAMPLING_RATE / 1e9:.0f} GS/s -> 1 ns"
)

# ---------------------------------------------------------------------------
# QUA: load_waveform then play. load_waveform stays outside strict_timing_.
# ---------------------------------------------------------------------------
with program() as duration_sweep:
    n = declare(int)
    i = declare(int)
    arr = declare(int)
    loc = declare(int)

    with for_(n, 0, n < N_AVG, n + 1):
        with for_(i, 0, i < n_points, i + 1):
            if n_arrays == 1:
                load_waveform(op_names[0], i, ELEMENT)
                with strict_timing_():
                    play(op_names[0], ELEMENT)
            else:
                assign(arr, i >> 10)  # i // 1024
                assign(loc, i - (arr << 10))
                with switch_(arr, unsafe=True):
                    for k, op in enumerate(op_names):
                        with case_(k):
                            load_waveform(op, loc, ELEMENT)
                            with strict_timing_():
                                play(op, ELEMENT)
            align()
            wait(COOLDOWN_CC)


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
        try:
            report = job.get_simulated_waveform_report()
            report.create_plot(samples, plot=True)
        except Exception as exc:
            print(f"Waveform report skipped: {exc}")
        plt.show()
    elif RUN_MODE == "execute":
        qm = qmm.open_qm(config)
        job = qm.execute(duration_sweep)
        job.result_handles.wait_for_all_values()
        print("Program finished on hardware.")
        plt.show()
    else:
        raise ValueError(f"Unknown RUN_MODE: {RUN_MODE!r}")
