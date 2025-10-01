'''
2025/09/30
CBO
Testing changes to VoltageGateSequence:
- When using an LF-FEM with a port in 'amplified' mode, voltage jumps of +/- 2V should not cause overflow of the `play` pulse.
- There should not be any issues when levels are QUA.
* Code must be tested on scope, since simulated waveforms do not match real outputs in case of overflow (for QOP350 and prior).
'''
# %%
# imports

from qm.qua import *
from qm import QuantumMachinesManager
from configuration_lf import *
import numpy as np
import plotly.graph_objects as go


# %%
# create VGS object
seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])


# %%
# define points
# P1 is symmetrical and should not have a compensation pulse
# pulse start
level_start = [0, 0]
duration_start = 10000
ramp_start = 0
# level 1
level_1 = [0.8, 0]
duration_1 = 2000
ramp_1 = 0
# level 2
level_2 = [0.9, 0]
duration_2 = 3000
ramp_2 = 0
# level 3
level_3 = [1, 0]
duration_3 = 2000
ramp_3 = 500
# level 4
level_4 = [-1, 0]   # -2V jump from level 3 to level 4
duration_4 = 3000
ramp_4 = 0          # ramp time must be zero to check large step
# zero level
level_zero = [0, 0]
duration_zero = 1000
ramp_zero = 0
# compensation
max_compensation_amplitude = 2.0

# %%
# Add the voltage points to VGS
seq.add_points("start", level_start, duration_start)
seq.add_points("level1", level_1, duration_1)
seq.add_points("level2", level_2, duration_2)
seq.add_points("level3", level_3, duration_3)
seq.add_points("level4", level_4, duration_4)
seq.add_points("zero", level_zero, duration_zero)


# %%
# construct the expected waveform without ramps
def get_linear_ramp(start_value, end_value, duration, sampling_rate=1):
    """
    Generates a list of points describing a linear ramp between two points.

    Args:
        start_value (float): The starting value of the ramp.
        end_value (float): The ending value of the ramp.
        duration (int): The duration of the ramp (in time units).
        sampling_rate (int, optional): Number of samples per time unit. Defaults to 1.

    Returns:
        list: List of float values representing the ramp.
    """
    num_points = duration*sampling_rate
    if num_points == 0:
        return []
    if num_points.is_integer():
        num_points = int(num_points)
    if num_points <= 1:
        return [start_value] * num_points
    ramp = [start_value + (end_value - start_value) * (i + 1) / (num_points) for i in range(num_points)]
    return ramp

requested_wf_p, requested_wf_m = [
    (
        [0]
        + get_linear_ramp(0, level_1[i], ramp_1, sampling_rate)
        + [level_1[i]] * duration_1 * sampling_rate
        + get_linear_ramp(level_1[i], level_2[i], ramp_2, sampling_rate)
        + [level_2[i]] * duration_2 * sampling_rate
        + get_linear_ramp(level_2[i], level_3[i], ramp_3, sampling_rate)
        + [level_3[i]] * duration_3 * sampling_rate
        + get_linear_ramp(level_3[i], level_4[i], ramp_4, sampling_rate)
        + [level_4[i]] * duration_4 * sampling_rate
        + get_linear_ramp(level_4[i], level_zero[i], ramp_zero, sampling_rate)
        + [level_zero[i]] * duration_zero * sampling_rate
    )
    for i in range(2)
]

# %%

# define the program 
with program() as prog:
    a = declare(int, value=duration_1)
    b = declare(int, value=ramp_3)
    c = declare(fixed, value=level_2[0])
    d = declare(fixed, value=level_2[1])
    with infinite_loop_():
        play("trigger", "qdac_trigger1")
        seq.add_step(voltage_point_name="start", ramp_duration=0) # check case where ramp_duration is zero 
        seq.add_step(voltage_point_name="level1", duration=a) # check case where duration is QUA
        seq.add_step(voltage_point_name="level2", level=[c, d]) # check case where level is QUA
        seq.add_step(voltage_point_name="level3", ramp_duration=b) # check case where ramp_duration is QUA  
        seq.add_step(voltage_point_name="level4", ramp_duration=ramp_4) 
        seq.add_step(voltage_point_name="zero", level=[0,0]) # check case where level is an integer
        seq.add_compensation_pulse(max_amplitude=max_compensation_amplitude) # P1 should have no compensation pulse
        seq.ramp_to_zero()


# %%
#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name, octave=octave_config)

###################
# Run the Program #
###################
# Open a quantum machine to execute the QUA program
qm = qmm.open_qm(config)
# Send the QUA program to the OPX, which compiles and executes it - Execute does not block python!
job = qm.execute(prog)

# %%
# check resulst on a scope and confirm that the output matchest the expected waveform
# plot the expected waveform
fig1 = go.Figure()
# x1 = np.linspace(0, len(requested_wf_p)-1, len(requested_wf_p))
fig1.add_trace(go.Scatter(
    y=requested_wf_p,
    mode='lines',
    line=dict(color='blue'),
    name='requested wf (P1)'
))
fig1.add_trace(go.Scatter(
    y=requested_wf_m,
    mode='lines',
    line=dict(color='red'),
    name='requested wf (P2)'
))

fig1.update_layout(
    legend=dict(title='Waveforms'),
    title='Requested waveforms',
    xaxis_title='t (ns)',
    yaxis_title='Amplitude (V)'
)
fig1.show()

