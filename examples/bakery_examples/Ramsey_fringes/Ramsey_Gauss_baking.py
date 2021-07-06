from qualang_tools.bakery import baking
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from RamseyGauss_configuration import *
from qm import SimulationConfig, LoopbackInterface

from matplotlib import pyplot as plt


baking_list = []  # Stores the baking objects
for i in range(number_of_pulses):  # Create 16 different baked sequences
    with baking(config, padding_method="left") as b:
        init_delay = number_of_pulses  # Put initial delay to ensure that all of the pulses will have the same length
        b.wait(
            init_delay, "Drive"
        )  # This is to compensate for the extra delay the Resonator is experiencing.
        # Play uploads the sample in the original config file (here we use an existing pulse in the config)
        b.play("gauss_drive", "Drive", amp=1)  # duration Tpihalf+16
        b.play_at("gauss_drive", "Drive", t=init_delay - i)  # duration Tpihalf

    # Append the baking object in the list to call it from the QUA program
    baking_list.append(b)


# You can retrieve and see the pulse you built for each baking object by modifying
# index of the waveform
plt.figure()
for i in range(number_of_pulses):
    baked_pulse = config["waveforms"][f"Drive_baked_wf_I_{i}"]["samples"]
    plt.plot(baked_pulse, label=f"pulse{i}")
plt.title("Baked Ramsey sequences")
plt.legend()


def play_ramsey():
    with switch_(j):
        for k in range(len(baking_list)):
            with case_(k):
                baking_list[k].run()


with program() as RamseyGauss:  # to measure Rabi flops every 1ns starting from 0ns
    timeout_counter = declare(int)
    I = declare(fixed, value=0.0)
    Q = declare(fixed)
    I1 = declare(fixed)
    Q1 = declare(fixed)
    I2 = declare(fixed)
    Q2 = declare(fixed)

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

    frame_rotation(angle, "Resonator")

    with for_(i_avg, 0, i_avg < 1000, i_avg + 1):
        with for_(d, 0, d < dmax, d + 4):
            with for_(j, 0, j < number_of_pulses, j + 1):
                reset_phase("Drive")
                align(
                    "Drive", "Resonator"
                )  # This align makes sure that the reset phase happens here.
                wait(
                    4 + 4 + d, "Drive"
                )  # 11 - resonator reset phase, 4 - wait inside the switch-case, 4 - switch-case delay
                play_ramsey()
                wait(drive_cc + d + 0, "Resonator")
                reset_phase("Resonator")
                play("chargecav", "Resonator")  # to charge the cavity

                measure(
                    "readout",
                    "Resonator",
                    None,
                    demod.full("integW_cos", I1, "out1"),
                    demod.full("integW_sin", Q1, "out1"),
                    demod.full("integW_cos", I2, "out2"),
                    demod.full("integW_sin", Q2, "out2"),
                )
                assign(
                    I, I1 + Q2
                )  # summing over all the items in the vectors before assigning to the final I and Q variables
                assign(Q, I2 - Q1)
                assign(pw, 4 * d + j)  # delay in ns between the 2 pihalf gauss pulses
                save(I, I_stream)
                save(Q, Q_stream)
                save(pw, param_stream)
                save(d, param2_stream)
                save(j, param2_stream)
        reset_frame("Drive")

    with stream_processing():
        I_stream.buffer(1000, npts).save("Iall")
        Q_stream.buffer(1000, npts).save("Qall")
        I_stream.buffer(1000, npts).save("IallNav")
        Q_stream.buffer(1000, npts).save("QallNav")
        # # I_stream.buffer(npts).buffer(N_averaging).map(FUNCTIONS.average()).save('I')
        # # Q_stream.buffer(npts).buffer(N_averaging).map(FUNCTIONS.average()).save('Q')
        param_stream.buffer(npts).average().save("param")
        param_stream.save_all("param2")
        param2_stream.buffer(2).save_all("param3")
        # timeout_stream.buffer(1000, npts).save('waitgs')

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
qmm = QuantumMachinesManager()
job = qmm.simulate(
    config,
    RamseyGauss,
    SimulationConfig(
        16 * (wait_time_cc + Readout_pulse_length + Fastload_length + drive_cc)
    ),
)
samps = job.get_simulated_samples()
plt.figure()
an1 = samps.con1.analog["1"].tolist()
an3 = samps.con1.analog["3"].tolist()
dig1 = samps.con1.digital["1"]
dig3 = samps.con1.digital["3"]

plt.plot(an1)
plt.plot(an3)

print("End prog")
plt.show()
print(job.result_handles.param2.fetch_all())
print(job.result_handles.param3.fetch_all())

plt.figure()
nz = np.nonzero(an1)[0][0]
index = 0
while nz < len(an1):
    start = nz - 10
    end = nz + 650
    plt.plot(an1[start:end])
    index += 1
    if len(np.nonzero(an1[end:])[0]) > 0:
        nz = np.nonzero(an1[end:])[0][0] + end
    else:
        nz = len(an1) + 1
