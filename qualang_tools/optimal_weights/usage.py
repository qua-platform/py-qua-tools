from qm import SimulationConfig, LoopbackInterface
from qualang_tools.optimal_weights.TwoStateDiscriminator_alpha import (
    TwoStateDiscriminator,
)
from configuration import *
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
import matplotlib.pyplot as plt
import numpy as np
from qm.simulate.credentials import create_credentials

N = 100
wait_time = 10
lsb = True
rr_qe = "rr1a"
res_pulse = "readout_pulse_g"
# qmm = QuantumMachinesManager(
#     host="nord-quantique-d14d58b1.quantum-machines.co",
#     port=443,
#     credentials=create_credentials(),
# )
qmm = QuantumMachinesManager(host="172.16.2.103", port="85")
discriminator = TwoStateDiscriminator(
    qmm=qmm,
    config=config,
    readout_el=rr_qe,
    readout_pulse=res_pulse,
    path=f"ge_disc_params_{rr_qe}.npz",
    meas_len=readout_len,
    smearing=smearing,
    lsb=lsb,
)

# gives you a template for training program
discriminator.get_default_training_program()
# Training
discriminator.train(plot=True, n_shots=1000, correction_method="mean")
discriminator.benchmark(n_shots=1000)




# result_handles = job.result_handles
# result_handles.wait_for_all_values()
# res = result_handles.get("res").fetch_all()["value"]
# I = result_handles.get("I").fetch_all()["value"]
# Q = result_handles.get("Q").fetch_all()["value"]
#
# plt.figure()
# plt.hist(I[np.array(seq0) == 0], 50)
# plt.hist(I[np.array(seq0) == 1], 50)
# plt.plot([discriminator.get_threshold()] * 2, [0, 60], "g")
# plt.show()
# plt.title("Histogram of |g> and |e> along I-values")
#
# # can only be used if signal was demodulated during training
# # with optimal integration weights
# plt.figure()
# plt.plot(I, Q, ".")  # measured IQ blobs
# # can only be used if raw ADC is passed to the program
# theta = np.linspace(0, 2 * np.pi, 100)
# for i in range(discriminator.num_of_states):
#     a = discriminator.sigma[i] * np.cos(theta) + discriminator.mu[i][0]
#     b = discriminator.sigma[i] * np.sin(theta) + discriminator.mu[i][1]
#     plt.plot([discriminator.mu[i][0]], [discriminator.mu[i][1]], "o")
#     plt.plot(a, b)
# plt.axis("equal")
#
# p_s = np.zeros(shape=(2, 2))
# for i in range(2):
#     res_i = res[np.array(seq0) == i]
#     # calculates the fidelity based on the number of shots
#     # in the correct and incorrect state
#     p_s[i, :] = np.array([np.mean(res_i == 0), np.mean(res_i == 1)])
#
# labels = ["g", "e"]
# plt.figure()
# ax = plt.subplot()
# # sns.heatmap(p_s, annot=True, ax=ax, fmt='g', cmap='Blues')
#
# ax.set_xlabel("Predicted labels")
# ax.set_ylabel("Prepared labels")
# ax.set_title("Confusion Matrix")
# ax.xaxis.set_ticklabels(labels)
# ax.yaxis.set_ticklabels(labels)
#
# plt.show()
