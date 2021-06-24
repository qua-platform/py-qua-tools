from qualang_tools.bakery import baking
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from RamseyGauss_configuration import *
from qm import SimulationConfig, LoopbackInterface

from matplotlib import pyplot as plt

dephasingStep = 0
number_of_pulses = 32
angle = np.pi / 4 + 0.65
dephasing0 = 0 #phase at the origin of the 2nd Tpihalf gauss pulse
npts = 48
Tpihalf = 32
wait_time_cc = 100
npts = 48
dmax = int(npts/4)
amplitude_pihalf = 1
drive_cc = int(Tpihalf/4) + 4 #12cc = 48ns for Tpihalf=32
if_freq = 31.25e6

baking_list = []  # Stores the baking objects
for i in range(number_of_pulses):  # Create 16 different baked sequences
    with baking(config, padding_method="left") as b:
        init_delay = number_of_pulses  # Put initial delay to ensure that all of the pulses will have the same length

        b.frame_rotation(dephasingStep, "Drive")
        b.wait(
            init_delay, "Drive"
        )  # This is to compensate for the extra delay the Resonator is experiencing.

        # Play uploads the sample in the original config file (here we use an existing pulse in the config)
        b.play("gauss_drive", "Drive", amp=1)  # duration Tpihalf+16
        b.play_at("gauss_drive", "Drive", init_delay - i)  # duration Tpihalf

    # Append the baking object in the list to call it from the QUA program
    baking_list.append(b)


# You can retrieve and see the pulse you built for each baking object by modifying
# index of the waveform
# plt.figure()
# for i in range(number_of_pulses):
#     baked_pulse = config["waveforms"][f"Drive_baked_wf_I_{i}"]["samples"]
#     t = np.arange(0, len(baked_pulse), 1)
#     plt.plot(t, baked_pulse)

def play_ramsey():
    with switch_(j):
        for i in range(16):
            with case_(i):
                wait(4, 'Drive')
                baking_list[i].run()


with program() as RamseyGauss:  # to measure Rabi flops every 1ns starting from 0ns
    timeout_counter = declare(int)
    I = declare(fixed, value=0.0)
    Q = declare(fixed)
    I1 = declare(fixed)
    Q1 = declare(fixed)
    I2 = declare(fixed)
    Q2 = declare(fixed)
    dephasing = declare(fixed)
    assign(dephasing, dephasing0)

    d = declare(int)
    pw = declare(int)
    j = declare(int)
    i_avg = declare(int)

    I_stream = declare_stream()
    Q_stream = declare_stream()
    # timeout_stream = declare_stream()
    param_stream = declare_stream()
    param2_stream = declare_stream()
    phase_stream = declare_stream()

    frame_rotation(angle, 'Resonator')
    frame_rotation(dephasing, 'Drive')

    with for_(i_avg, 0, i_avg < 1000, i_avg + 1):
        frame_rotation_2pi((-Tpihalf / 65 + 0.508) * 0.032 * if_freq / 1e6, 'Drive')
        with for_(d, 0, d < dmax, d + 4):
            frame_rotation_2pi(1 - 0.016 * if_freq / 1e6, 'Drive')
            with for_(j, 0, j < 16, j + 1):
                # wait(wait_time_cc, 'Drive', 'Drive2', 'Resonator')
                align('Drive', 'Resonator')
                frame_rotation(dephasingStep, 'Drive')
                reset_phase('Drive')
                align('Drive', 'Resonator')  # This align makes sure that the reset phase happens here.
                wait(11 + 4 + 4 + d,
                     'Drive')  # 11 - resonator reset phase, 4 - wait inside the switch-case, 4 - switch-case delay
                play_ramsey()

                play('gauss_drive' * amp(amplitude_pihalf), 'Drive')  # duration Tpihalf
                wait(drive_cc + d + 0, 'Resonator')
                reset_phase('Resonator')
                play("chargecav", "Resonator")  # to charge the cavity
                measure("readout", "Resonator", None, dual_demod.full("integW_cos", "out1", "integW_sin", "out2", I))
                save(I, I_stream)
                assign(dephasing, dephasing + dephasingStep)
                assign(pw, 4 * d + j)  # delay in ns between the 2 pihalf gauss pulses
                save(pw, param_stream)
                save(d, param2_stream)
                save(j, param2_stream)
                save(dephasing, phase_stream)  # dephasing of the 2nd gauss pulse wrt 1st one
        reset_frame('Drive')

    with stream_processing():
        I_stream.buffer(1000, npts).save('Iall')
        # Q_stream.buffer(1000, npts).save('Qall')
        # I_stream.buffer(1000, npts).save('IallNav')
        # Q_stream.buffer(1000, npts).save('QallNav')
        # # I_stream.buffer(npts).buffer(N_averaging).map(FUNCTIONS.average()).save('I')
        # # Q_stream.buffer(npts).buffer(N_averaging).map(FUNCTIONS.average()).save('Q')
        param_stream.buffer(npts).average().save('param')
        param_stream.save_all('param2')
        param2_stream.buffer(2).save_all('param3')
        # phase_stream.buffer(npts).average().save('dephasing')
        # timeout_stream.buffer(1000, npts).save('waitgs')

simulation_config = SimulationConfig(
    duration=int(4e5),  # need to run the simulation for long enough to get all points
    simulation_interface=LoopbackInterface(
        [("con1", 1, "con1", 1), ("con1", 2, "con1", 2)],
        noisePower=0.05 ** 2,
    ),
)

qmm = QuantumMachinesManager()
job = qmm.simulate(config, RamseyGauss, simulation_config)
samples = job.get_simulated_samples()
# samples.con1.plot()
# job = qm.execute(RamseyGauss)
# res = job.result_handles
# sleep(2)

# I = np.array(res.I.fetch_all()) * Inverse_Readout_pulse_length
# Q = np.array(res.Q.fetch_all()) * Inverse_Readout_pulse_length
# time = np.array(res.param.fetch_all())  # in ns

"""
plt.ion()
fig, ax = plt.subplots(2,1)
I_plot, = ax[0].plot(dur, I_vs_dur)
Q_plot, = ax[1].plot(dur, Q_vs_dur)
ax[0].grid()
ax[1].grid()
plt.show()

ax[0].set_title("Rabi 1ns", fontsize=18)
ax[1].set_xlabel("drive duration (ns)", fontsize=14)
ax[0].set_ylabel("I", fontsize=14)
ax[1].set_ylabel("Q", fontsize=14)
while True:
    print("tic")
    I_vs_dur = np.array(res.I.fetch_all()) * Inverse_Readout_pulse_length
    Q_vs_dur = np.array(res.Q.fetch_all()) * Inverse_Readout_pulse_length
    dur = np.array(res.param.fetch_all())  # in ns
    I_plot.set_ydata(I_vs_dur)
    Q_plot.set_ydata(Q_vs_dur)
    fig.canvas.draw()
    fig.canvas.flush_events()
    sleep(2)
"""
