import os
from pathlib import Path

import numpy as np

from qualang_tools.config import convert_integration_weights
from qualang_tools.config.integration_weights_tools import compress_integration_weights


def abs_path_to(rel_path: str) -> str:
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    return os.path.join(source_dir, rel_path)


def test_validity_arbitrary_integration_weights():
    weights_before = np.load(abs_path_to("iw1_cos1.npy")).tolist()
    weights_after = convert_integration_weights(weights_before, N=len(weights_before))
    ii = 0
    for i in range(len(weights_after) // 4):
        for j in range(weights_after[i][1] // 4):
            assert np.abs(weights_after[i][0] - weights_before[ii]) < 2**-15
            ii += 1
    assert sum([i[1] for i in weights_after]) == 4 * len(weights_before)


def test_compression_arbitrary_integration_weights():
    weights_before = np.load(abs_path_to("iw1_cos1.npy")).tolist()
    weights_after = convert_integration_weights(weights_before, N=500)
    assert sum([i[1] for i in weights_after]) == 4 * len(weights_before)


def test_compress_integration_weights_respects_max_length():
    weights = [(0.01 * i, 4) for i in range(30)]
    compressed = compress_integration_weights(weights, N=5, plot=False)
    assert len(compressed) <= 5
    assert sum(item[1] for item in compressed) == 4 * 30
