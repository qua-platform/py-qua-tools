"""
Squares (Python + QUA) + Ramps (None) + Compensation (max_amplitude=0.45)
"""

from qm import generate_qua_script
from qm.qua import *
from validation_utils import *


###################
# The QUA program #
###################


# %% 1 consecutive compensation pulses
print("1 single compensation pulse:")
level_init = [MAX_AMP, -0.1]
duration_init = 1000
level_manip = [0.5, -0.3]
duration_manip = 100
level_readout = [0.2, -0.2]
duration_readout = 2000
max_compensation_amplitude = 0.2

# Add the relevant voltage points describing the "slow" sequence (no qubit pulse)
seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])
seq.add_points("initialization", level_init, duration_init)
seq.add_points("idle", level_manip, duration_manip)
seq.add_points("readout", level_readout, duration_readout)


requested_wf_p, requested_wf_m = [
    (
        [level_init[i]] * duration_init * sampling_rate
        + [level_manip[i]] * duration_manip * sampling_rate
        + [level_readout[i]] * duration_readout * sampling_rate
    )
    for i in range(2)
]


with program() as prog:
    a = declare(fixed, value=level_init[0])
    b = declare(fixed, value=level_init[1])
    with infinite_loop_():
        play("trigger", "qdac_trigger1")
        seq.add_step(voltage_point_name="initialization", level=[a, b])
        seq.add_step(voltage_point_name="idle")
        seq.add_step(voltage_point_name="readout")
        seq.add_compensation_pulse(max_amplitude=max_compensation_amplitude)
        seq.ramp_to_zero()

# %% Simulate the QUA program and validate it with the simulator
qmm, samples = simulate_program(prog, simulation_duration=30000)
validate_program(samples, requested_wf_p, requested_wf_m)

# print(generate_qua_script(prog, config))

# %% 2 consecutive compensation pulses
level_init = [MAX_AMP, -0.1]
duration_init = 3000
level_manip = [0.5, -0.3]
duration_manip = 100
level_readout = [0.2, -0.2]
duration_readout = 2000
max_compensation_amplitude = 0.45

# Add the relevant voltage points describing the "slow" sequence (no qubit pulse)
seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])
seq.add_points("initialization", level_init, duration_init)
seq.add_points("idle", level_manip, duration_manip)
seq.add_points("readout", level_readout, duration_readout)


requested_wf_p, requested_wf_m = [
    (
        [level_init[i]] * duration_init * sampling_rate
        + [level_manip[i]] * duration_manip * sampling_rate
        + [level_readout[i]] * duration_readout * sampling_rate
    )
    for i in range(2)
]


with program() as prog:
    a = declare(fixed, value=level_init[0])
    b = declare(fixed, value=level_init[1])
    with infinite_loop_():
        play("trigger", "qdac_trigger1")
        seq.add_step(voltage_point_name="initialization", level=[a, b])
        seq.add_step(voltage_point_name="idle")
        seq.add_step(voltage_point_name="readout")
        seq.add_compensation_pulse(max_amplitude=max_compensation_amplitude)
        seq.ramp_to_zero()

# %% Simulate the QUA program and validate it with the simulator
qmm, samples = simulate_program(prog, simulation_duration=30000)
validate_program(samples, requested_wf_p, requested_wf_m)

# print(generate_qua_script(prog, config))
# qm = qmm.open_qm(config)
# job=qm.execute(prog)
