'''
2025/09/25
CBO
Testing changes to VoltageGateSequence:
- ramp durations of 0ns should not cause errors
- sequences with average voltage of 0V should not have a compensation pulse
- voltage levels of "0" after levels with QUA variables should not cause issues
'''
# %%
# imports

from qm.qua import *
from validation_utils_v2 import *


# %%
# create VGS object
seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])


# %%
# define points
# P1 is symmetrical and should not have a compensation pulse
# pulse start
level_start = [0, 0]
duration_start = 200
# init
level_init = [0.15, 0.10]
duration_init = 200
# manip1
level_manip = [0.25, 0.2]
duration_manip = 300
# manip2
level_manip2 = [-0.25, 0.05]
duration_manip2 = 300
ramp_manip2 = 400
# readout
level_readout = [-0.15, -0.05]
duration_readout = 200
# zero
level_zero = [0, 0]
duration_zero = 20
# compensation
max_compensation_amplitude = 0.45

# %%
# Add the voltage points to VGS
seq.add_points("start", level_start, duration_start)
seq.add_points("initialization", level_init, duration_init)
seq.add_points("manip", level_manip, duration_manip)
seq.add_points("manip2", level_manip2, duration_manip2)
seq.add_points("readout", level_readout, duration_readout)
seq.add_points("zero", level_zero, duration_zero)

# %%
# construct the expected waveform without ramps
requested_wf_p, requested_wf_m = [
    (
        [0]
        + [level_init[i]] * duration_init * sampling_rate
        + [level_manip[i]] * duration_manip * sampling_rate
        + get_linear_ramp(level_manip[i], level_manip2[i], ramp_manip2, sampling_rate)
        + [level_manip2[i]] * duration_manip2 * sampling_rate
        + [level_readout[i]] * duration_readout * sampling_rate
        + [level_zero[i]] * duration_zero * sampling_rate
    )
    for i in range(2)
]

# %%
# define the program 
with program() as prog:
    a = declare(int, value=duration_init)
    b = declare(int, value=ramp_manip2)
    c = declare(fixed, value=level_readout[0])
    d = declare(fixed, value=level_readout[1])
    with infinite_loop_():
        play("trigger", "qdac_trigger1")
        seq.add_step(voltage_point_name="start") 
        seq.add_step(voltage_point_name="initialization", duration=a) # check case where duration is QUA
        seq.add_step(voltage_point_name="manip", ramp_duration=0) # check case where ramp_duration = 0
        seq.add_step(voltage_point_name="manip2", ramp_duration=b) # check case where ramp_duration is QUA  
        seq.add_step(voltage_point_name="readout", level=[c, d]) # check case where level is QUA 
        seq.add_step(voltage_point_name="zero", level=[0,0]) # check case where level is an integer
        seq.add_compensation_pulse(max_amplitude=max_compensation_amplitude) # P1 should have no compensation pulse
        seq.ramp_to_zero()

# %%
# run the program
qmm, samples = simulate_program(prog, simulation_duration=30000)

# %%
# validate the results
# plot_pulses(samples, requested_wf_p, requested_wf_m)
validate_program_v2(samples, requested_wf_p, requested_wf_m, time=2500)

# %%
