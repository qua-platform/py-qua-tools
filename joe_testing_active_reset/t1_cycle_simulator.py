"""
Created on 04/08/2022
@author jdh
"""

from sample_generator import _generate_spin_samples

import numpy as np


def t1_cycle(v_rf_s, v_rf_t, sigma, T1, number_of_samples, triplet_probability, integration_time):
    """
    :param v_rf_s: mean singlet measurement value
    :param v_rf_t: mean triplet measurement value
    :param sigma: gaussian measurement noise
    :param T1: rate parameter for average spin lifetime
    :param number_of_samples: self
    :param triplet_probability: probability of loading a triplet for each measurement (stick to 0.5)
    :param integration_time: integration time for each measurement
    :return: simulated data for a rabi experiment
    """

    # draw samples. 0 means singlet, 1 means triplet
    triplets = np.random.binomial(1, triplet_probability, number_of_samples)

    return _generate_spin_samples(v_rf_s, v_rf_t, sigma, T1, number_of_samples, integration_time, triplets)

