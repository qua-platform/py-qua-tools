from dataclasses import dataclass
from typing import Callable

from qualang_tools.bakery.bakery import baking, Baking
import numpy as np

rnd_gate_list = ["sx", "sy", "sw", "id"]

op_func = Callable[[Baking], None]


@dataclass
class XEBOpsSingleQubit:
    """
    A class for representing the XEB operations. Each callable corresponds to a function with a baking object as argument,
    and performs the operations in the body of the function.

    Operations defined in this class correspond to single qubit operations
    """

    id: op_func
    sx: op_func
    sy: op_func
    sw: op_func


class XEB:
    def __init__(
        self,
        config: dict,
        m_max: int,
        q1_ops: XEBOpsSingleQubit,
        q2_ops: XEBOpsSingleQubit,
        two_qubit_op: op_func,
        align_op: op_func,
    ):
        """
        Class instance for cross-entropy benchmarking sequence generation.

        :param config: Configuration file
        :param m_max: Maximum length of XEB sequence
        :param q1_ops: operations dataclass which maps single qubit operations to series of operations for qubit 1
        :param q2_ops: operations dataclass which maps single qubit operations to series of operations for qubit 2
        :param two_qubit_op: a callable with baking object as argument that performs the two qubit operation
        :param align_op: a callable with baking object as argument that performs an align operation on all quantum elements

        """
        self.config = config
        self.m_max = m_max
        self.duration_tracker = [0] * m_max
        self.operations_list = {qe: [] for qe in ["q1", "q2"]}
        self.baked_sequence = self._generate_xeb_sequence(q1_ops, q2_ops, two_qubit_op, align_op)

    def _generate_xeb_sequence(self, q1_ops, q2_ops, two_qubit_op, align_op):
        rand_seq1 = np.random.randint(3, size=self.m_max)
        rand_seq2 = np.random.randint(3, size=self.m_max)

        with baking(self.config) as b_2_qubit:
            two_qubit_op(b_2_qubit)

        b_2_qubit_len = get_total_len(b_2_qubit)

        b_q1 = []
        q1_len = 0
        for op in rnd_gate_list:
            with baking(self.config) as btemp:
                getattr(q1_ops, op)(btemp)
            b_q1.append(btemp)
            q1_len = max(q1_len, get_total_len(btemp))

        b_q2 = []
        q2_len = 0
        for op in rnd_gate_list:
            with baking(self.config) as btemp:
                getattr(q2_ops, op)(btemp)
            b_q2.append(btemp)
            q2_len = max(q2_len, get_total_len(btemp))

        with baking(self.config) as b_main:
            i = 0
            for rnd1, rnd2 in zip(rand_seq1, rand_seq2):
                align_op(b_main)
                play_all_ops(b_main, b_q1[rnd1])
                play_all_ops(b_main, b_q2[rnd2])
                align_op(b_main)
                play_all_ops(b_main, b_2_qubit)
                align_op(b_2_qubit)
                self.operations_list["q1"].append(rnd_gate_list[rnd1])
                self.operations_list["q2"].append(rnd_gate_list[rnd2])
                self.duration_tracker[i] = max(q1_len, q2_len) + b_2_qubit_len
                i += 1
            play_all_ops(b_main, b_q1[3])
            play_all_ops(b_main, b_q2[3])
        self.duration_tracker = np.cumsum(self.duration_tracker).tolist()
        return b_main


def play_all_ops(current_bake, sub_bake):
    for element in sub_bake.elements:
        current_bake.play(sub_bake.operations[element], element)


def get_total_len(baking_sequence):
    return max(baking_sequence.get_op_length(element) for element in baking_sequence.elements)
