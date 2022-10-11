"""
Created on 04/08/2022
@author jdh
"""

import numpy as np


# runs at around 0.1 ns per sample (2000 samples in ~200 us)
# obviously big overhead if doing small number of samples.
def _generate_spin_samples(v_rf_s, v_rf_t, sigma, T1, number_of_samples, integration_time, triplets):
    """
    triplets tells you which samples are triplets (to start with). This way this method can be used to simulate
    rabi or t1 cycle
    Triplets have a probability of decaying set by the decay rate.
    :param number_of_samples:
    :param triplet_probability:
    :return:
    """



    # quicker to generate all the samples first and then pick which ones we want
    # based on the variable above (triplets)

    singlet_samples = np.random.normal(
        loc=v_rf_s,
        scale=sigma,
        size=number_of_samples
    )

    singlet_samples_for_triplet_decay = np.random.normal(
        loc=v_rf_s,
        scale=sigma,
        size=number_of_samples
    )

    triplet_samples = np.random.normal(
        loc=v_rf_t,
        scale=sigma,
        size=number_of_samples
    )

    # add decay to the tT1,riplet samples
    # ratio of decay time to integration time gives how far along
    # v axis that samples moves towards singlet (representing it decaying
    # at some point through the measurement window)

    decay_times = np.random.exponential(
        scale=T1,
        size=number_of_samples
    )

    # how much of the measurement was a triplet is given by this ratio.
    # clipped to be max 1
    triplet_contribution = np.clip(
        decay_times / integration_time, 0, 1
    )

    decayed_triplet_samples = (triplet_contribution * triplet_samples) + (
            (1 - triplet_contribution) * singlet_samples_for_triplet_decay
    )

    return np.where(triplets, decayed_triplet_samples, singlet_samples)