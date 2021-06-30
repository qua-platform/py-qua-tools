from qualang_tools.bakery import baking
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from RamseyGauss_configuration import *
from qm import SimulationConfig, LoopbackInterface

from matplotlib import pyplot as plt

n = 1
baking_list = []  # Stores the baking objects
for i in range(n):  # Create 16 different baked sequences
    with baking(config, padding_method="left") as b:
        init_delay = number_of_pulses  # Put initial delay to ensure that all of the pulses will have the same length
        b.wait(init_delay, "Drive")  # This is to compensate for the extra delay the Resonator is experiencing.
        # Play uploads the sample in the original config file (here we use an existing pulse in the config)
        b.play("gauss_drive", "Drive", amp=1)  # duration Tpihalf+16
        b.update_frequency("Drive", 1e7)
        b.play("gauss_drive", "Drive")
        # b.play_at("gauss_drive", "Drive", t=init_delay - i)  # duration Tpihalf

    # Append the baking object in the list to call it from the QUA program
    baking_list.append(b)


# You can retrieve and see the pulse you built for each baking object by modifying
# index of the waveform
plt.figure()
for i in range(n):
    baked_pulse_I = config["waveforms"][f"Drive_baked_wf_I_{i}"]["samples"]
    baked_pulse_Q = config["waveforms"][f"Drive_baked_wf_Q_{i}"]["samples"]
    plt.plot(baked_pulse_I, label=f'pulse{i}')
    plt.plot(baked_pulse_Q)
plt.title('Baked Ramsey sequences')
plt.legend()

with program() as prog:
    play("gauss_drive", "Drive")
    update_frequency("Drive", 1e7)
    play("gauss_drive", "Drive")

qmm = QuantumMachinesManager()
job = qmm.simulate(config, prog,
                   SimulationConfig(125))
plt.figure()
samps = job.get_simulated_samples()
samps.con1.plot()