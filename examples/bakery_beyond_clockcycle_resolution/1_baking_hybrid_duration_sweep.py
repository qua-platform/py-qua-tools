"""
Sweep a square pulse's duration 1 ns -> 1 us in 1 ns steps, without baking
every length.

OPX1000 analog pulses must be >= 16 ns and a multiple of 4 ns, so a naive
1 ns loop would need ~1000 baked pulses. Instead, bake only the illegal
lengths (1..15 ns) and split every other T:

    T_main = T - (T % 4)  ->  play(..., duration=T_main // 4)  (>= 16 ns, real-time)
    T_rem  = T % 4        ->  baked pulse (0..3 ns, skipped if 0)

e.g. 27 ns = play(duration=6) [24 ns] + baked 3 ns. This concatenation is
exact only because a square is constant-amplitude; it would NOT hold for a
duration-dependent shape like a Gaussian (see example 2).
"""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from qm import QuantumMachinesManager, SimulationConfig, generate_qua_script
from qm.qua import (
    align,
    assign,
    case_,
    declare,
    else_,
    for_,
    if_,
    play,
    program,
    switch_,
    wait,
)
from qualang_tools.bakery import baking

# ---------------------------------------------------------------------------
# Hardware / experiment knobs
# ---------------------------------------------------------------------------
CON = "con1"
MW_FEM = 1
MW_PORT = 1
MW_BAND = 2
UPCONVERTER_HZ = 5.0e9
QUBIT_IF_HZ = 100e6
FULL_SCALE_POWER_DBM = 1
ELEMENT = "qubit"

MIN_PULSE_NS = 16  # OPX analog minimum
CLOCK_NS = 4
SQUARE_AMP = 0.3  # fraction of full_scale_power_dbm, in [-1, 1]

DURATION_MIN_NS = 1
DURATION_MAX_NS = 1000  # 1 us
DURATION_STEP_NS = 1

HOST_IP = "qop_ip"
CLUSTER_NAME = "cluster_name"

# "bake_only" — bake + plot envelopes, no OPX
# "compile"   — also print the generated QUA script
# "simulate"  — QMM simulation
# "execute"   — run on hardware
RUN_MODE = "bake_only"
SIMULATION_DURATION_NS = 20_000
N_AVG = 10
COOLDOWN_CC = 100  # 4 ns clock cycles between shots

# ---------------------------------------------------------------------------
# Minimal OPX1000 / MW-FEM config: 16 ns constant (duration-parameterized)
# ---------------------------------------------------------------------------
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
                "square": "square_pulse",
            },
        },
    },
    "pulses": {
        "square_pulse": {
            "operation": "control",
            "length": MIN_PULSE_NS,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        },
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": SQUARE_AMP},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
}

# ---------------------------------------------------------------------------
# Bake only illegal lengths: 1 ns .. 15 ns (below 16 ns and/or not multiple of 4)
# Remainders 1, 2, 3 ns for T >= 16 reuse these same baked pulses.
# padding_method="right": the square starts immediately, zeros fill to 16 ns
# so a remainder concatenates onto play(..., duration=...) without a leading gap.
# ---------------------------------------------------------------------------
baked_by_ns = {}
for t_ns in range(1, MIN_PULSE_NS):
    i_wf = [SQUARE_AMP] * t_ns
    q_wf = [0.0] * t_ns
    with baking(config, padding_method="right") as b:
        b.add_op("square_short", ELEMENT, [i_wf, q_wf])
        b.play("square_short", ELEMENT)
    baked_by_ns[t_ns] = b

print(f"Baked {len(baked_by_ns)} waveforms (1..{MIN_PULSE_NS - 1} ns).")
print(
    f"Duration sweep: {DURATION_MIN_NS} -> {DURATION_MAX_NS} ns "
    f"in {DURATION_STEP_NS} ns steps "
    f"({(DURATION_MAX_NS - DURATION_MIN_NS) // DURATION_STEP_NS + 1} points)."
)


def split_duration(t_ns: int) -> tuple[int, int]:
    """Return (T_main_ns, T_rem_ns) as played in QUA."""
    if t_ns < MIN_PULSE_NS:
        return 0, t_ns
    rem = t_ns % CLOCK_NS
    return t_ns - rem, rem


print("")
print("  T (ns)   regular play         baked play")
for t_ns in (1, 3, 7, 12, 15, 16, 17, 20, 24, 27, 28, 100, 1000):
    main, rem = split_duration(t_ns)
    if main == 0:
        regular = "-"
    else:
        regular = f"duration={main // CLOCK_NS:4d} cc ({main} ns)"
    baked = f"{rem} ns" if rem else "-"
    print(f"  {t_ns:6d}   {regular:28s} {baked}")

# ---------------------------------------------------------------------------
# Plot baked shorts + a reconstructed 27 ns hybrid vs a true 27 ns square
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)

for t_ns in (1, 3, 7, 12, 15):
    samples = np.array(config["waveforms"][f"{ELEMENT}_baked_wf_I_{t_ns - 1}"]["samples"])
    axes[0].step(
        np.arange(len(samples)),
        samples,
        where="post",
        marker="o",
        markersize=3,
        label=f"{t_ns} ns",
    )

axes[0].set_title("Baked illegal lengths (padded to 16 ns)")
axes[0].set_xlabel("Time (ns)")
axes[0].set_ylabel("I amplitude (full-scale fraction)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 27 ns = 24 ns constant play + baked 3 ns constant (+ 13 ns right-pad zeros).
example_t = 27
main_ns, rem_ns = split_duration(example_t)
main_part = np.full(main_ns, SQUARE_AMP)
baked_rem = np.array(config["waveforms"][f"{ELEMENT}_baked_wf_I_{rem_ns - 1}"]["samples"])
hybrid = np.concatenate([main_part, baked_rem])
true_square = np.full(example_t, SQUARE_AMP)
t_hybrid = np.arange(len(hybrid))
axes[1].step(t_hybrid, hybrid, where="post", color="C0", linewidth=2, label="24 ns play + 3 ns baked")
axes[1].step(
    np.arange(example_t),
    true_square,
    where="post",
    color="C1",
    linestyle="--",
    linewidth=2,
    label="true 27 ns square",
)
axes[1].axvspan(0, main_ns, color="C0", alpha=0.12, label=f"play duration={main_ns // CLOCK_NS} cc")
axes[1].axvspan(main_ns, main_ns + rem_ns, color="C1", alpha=0.25, label=f"baked {rem_ns} ns")
axes[1].axvline(example_t, color="k", linestyle="--", linewidth=1, label=f"T = {example_t} ns")
axes[1].set_title(f"{example_t} ns hybrid matches a true {example_t} ns square")
axes[1].set_xlabel("Time (ns)")
axes[1].set_ylabel("I amplitude (full-scale fraction)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)
axes[1].set_ylim(-0.02, SQUARE_AMP * 1.25)

fig.suptitle("Hybrid square duration sweep: bake 1-15 ns, play + remainder above 16 ns")

# ---------------------------------------------------------------------------
# QUA program: real-time duration loop (no Python unroll of 1000 points)
# Bake *before* opening a QuantumMachine — baking edits ``config``.
# ---------------------------------------------------------------------------
with program() as duration_sweep:
    n = declare(int)
    t = declare(int)  # pulse duration in ns
    t_cycles = declare(int)  # 4 ns clock cycles for play(..., duration=)
    t_rem = declare(int)  # 0..3 ns remainder

    with for_(n, 0, n < N_AVG, n + 1):
        with for_(t, DURATION_MIN_NS, t <= DURATION_MAX_NS, t + DURATION_STEP_NS):
            with if_(t < MIN_PULSE_NS):
                with switch_(t, unsafe=True):
                    for t_ns in range(1, MIN_PULSE_NS):
                        with case_(t_ns):
                            baked_by_ns[t_ns].run()
            with else_():
                assign(t_cycles, t >> 2)  # t // 4
                assign(t_rem, t - (t_cycles << 2))  # t % 4
                with if_(t_rem > 0):
                    with switch_(t_rem, unsafe=True):
                        # only python loop works here because baked_by_ns
                        # is a dictionary with python variable as keys
                        for rem in (1, 2, 3):
                            with case_(rem):
                                play("square", ELEMENT, duration=t_cycles)
                                baked_by_ns[rem].run()
                with else_():
                    play("square", ELEMENT, duration=t_cycles)
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
