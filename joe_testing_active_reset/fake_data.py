import numpy as np
import matplotlib.pyplot as plt

from t1_cycle_simulator import t1_cycle





def active_reset_experiment_simulator(v_0, v_1, sigma, num_samples, threshold):

    # generate random sample


    # based on that sample, if high state reset to low state

    #     measure
    pass

v_0 = 0.001
v_1 = 0.01
sigma = 0.04 ** 2
T1 = 350e-6
integration_time = 15e-6
num_samples = 4000
prob_state_1 = 0.5

data = t1_cycle(v_0, v_1, sigma,T1, num_samples, prob_state_1, integration_time)

plt.figure()
plt.hist(data, bins=30)
plt.xlim([-0.04, 0.04])
plt.show()


