import pytest
import numpy as np
from qualang_tools import *
import matplotlib.pyplot as plt
import os


def test_validity_arbitrary_integration_weights():
    weights_before = np.load('iw1_cos1.npy')
    weights_after = convert_integration_weights(weights_before, N=len(weights_before))
    ii = 0
    for i in range(len(weights_after)//4):
        for j in range(weights_after[i][1]//4):
            assert(np.abs(weights_after[i][0] - weights_before[ii]) < 2 ** -15)
            ii += 1
    assert(sum([i[1] for i in weights_after]) == 4*len(weights_before))


def test_compression_arbitrary_integration_weights():
    weights_before = np.load('iw1_cos1.npy')
    weights_after = convert_integration_weights(weights_before, N=500)
    assert(sum([i[1] for i in weights_after]) == 4*len(weights_before))