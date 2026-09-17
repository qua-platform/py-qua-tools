from copy import deepcopy

import pytest

from qualang_tools.bakery.randomized_benchmark import RBOneQubit, find_revert_op
from qualang_tools.bakery.randomized_benchmark_c1 import c1_ops, c1_table
from tests.test_xeb import bakery_config


def _ops_config():
    cfg = deepcopy(bakery_config())
    clifford_ops = {
        "I",
        "X",
        "Y",
        "X/2",
        "-X/2",
        "Y/2",
        "-Y/2",
    }
    for name in clifford_ops:
        cfg["elements"]["qe1"]["operations"][name] = "constPulse"
    return cfg


def test_find_revert_op_identity_row():
    for state_index in range(len(c1_ops)):
        revert = find_revert_op(state_index)
        assert c1_table[state_index][revert] == 0


def test_rb_one_qubit_construction():
    rb = RBOneQubit(_ops_config(), d_max=4, K=2, qubit="qe1")

    assert len(rb.sequences) == 2
    assert len(rb.inverse_ops) == 2
    assert len(rb.baked_sequences) == 2
    for seq in rb.sequences:
        assert len(seq.operations_list) == 4
        assert all(op is not None for op in seq.operations_list)


def test_rb_one_qubit_missing_element():
    with pytest.raises(KeyError, match="not in the config"):
        RBOneQubit(bakery_config(), d_max=2, K=1, qubit="missing")
