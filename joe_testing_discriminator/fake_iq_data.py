import numpy as np
import matplotlib.pyplot as plt

from qualang_tools.analysis.discriminator import two_state_discriminator

# generate some fake readout data in i and q planes 
# I is x, Q is y

iq_state_g = np.random.multivariate_normal((0, -0.2), ((0.5, 0.), (0., 0.5)), 5000).T
iq_state_e = np.random.multivariate_normal((-1.8, -3.), ((0.5, 0), (0, 0.5)), 5000).T

# plot to check

plt.scatter(*iq_state_g, label='ground')
plt.scatter(*iq_state_e, label='excited')
plt.legend()
plt.show()



Ig, Qg = iq_state_g
Ie, Qe = iq_state_e


angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(Ig, Qg, Ie, Qe, b_print=True, b_plot=True)





