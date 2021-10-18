from qualang_tools.bakery import baking
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from RamseyGauss_configuration import *
from qm import SimulationConfig
from matplotlib import pyplot as plt
from qualang_tools.bakery.bakery import deterministic_run

sample_rate = 3e9
t_max *= int(sample_rate / 1e9)

baking_list = []  # Stores the baking objects
# Create the different baked sequences, corresponding to the different taus
for i in range(t_max):
    with baking(config, padding_method="left", sampling_rate=sample_rate) as b:
        init_delay = t_max  # Put initial delay to ensure that all of the pulses will have the same length
        b.wait(init_delay, "drive")  # We first wait the entire duration.

        # We add the 2nd pi_half pulse with the phase 'dephasing' (Confusingly, the first pulse will be added later)
        # Play uploads the sample in the original config file (here we use an existing pulse in the config)
        b.frame_rotation(dephasing, "drive")
        b.play("pi_half", "drive")

        # We add the 1st pi_half pulse. It will be added with the frame at time init_delay - i, which will be 0.
        b.play_at("pi_half", "drive", t=init_delay - i)
        # We reset frame such that we will not accumulate phase between iterations.
        b.reset_frame("drive")

    # Append the baking object in the list to call it from the QUA program
    baking_list.append(b)


# You can retrieve and see the pulse you built for each baking object by modifying
# index of the waveform
plt.figure()
for i in range(t_max):
    baked_pulse = config["waveforms"][f"drive_baked_wf_I_{i}"]["samples"]
    plt.plot(baked_pulse, label=f"pulse{i}")
plt.title("Baked Ramsey sequences")
plt.legend()


with program() as RamseyGauss:  # to measure Rabi flops every 1ns starting from 0ns
    I = declare(fixed, value=0.0)
    Q = declare(fixed)
    I1 = declare(fixed)
    Q1 = declare(fixed)
    I2 = declare(fixed)
    Q2 = declare(fixed)

    j = declare(int)
    i_avg = declare(int)

    I_stream = declare_stream()
    Q_stream = declare_stream()

    with for_(i_avg, 0, i_avg < 1000, i_avg + 1):
        with for_(j, 0, j < t_max, j + 1):
            # Wait for cavity cooldown, very short just for the example.
            wait(10)

            deterministic_run(baking_list, j, unsafe=True)
            # The following wait command is used to align the resonator to happen right after the pulse.
            # In this specific example, an align() command would have added a slight gap.
            wait(drive_cc, "resonator")
            play("chargecav", "resonator")  # to charge the cavity

            measure(
                "readout",
                "resonator",
                None,
                demod.full("cos", I1, "out1"),
                demod.full("sin", Q1, "out1"),
                demod.full("cos", I2, "out2"),
                demod.full("sin", Q2, "out2"),
            )
            assign(I, I1 + Q2)
            assign(Q, I2 - Q1)
            save(I, I_stream)
            save(Q, Q_stream)

    with stream_processing():
        I_stream.buffer(t_max).average().save("Iall")
        Q_stream.buffer(t_max).average().save("Qall")

qmm = QuantumMachinesManager()
job = qmm.simulate(
    config,
    RamseyGauss,
    SimulationConfig(
        17 * (wait_time_cc + readout_pulse_length + drive_cc) * int(sample_rate / 1e9)
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

plt.show()
