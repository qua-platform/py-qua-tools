from qualang_tools.characterization.two_qubit_rb.analysis.fitting import DoubleExponentialFit, TwoQubitRbFit


def calculate_average_two_qubit_clifford_fidelity(fit: TwoQubitRbFit) -> float:
    """
    Calculates the average 2Q Clifford gate-set fidelity.

    If leakage data is present, subtracts leakage error, then the
    leakage error is removed from the final calculation, according to
    the Leakage Randomized Benchmarking protocol by Wood & Gambetta.

    Returns:
        float: Estimated average fidelity per Clifford.

    References:
        Wood, C.J. and Gambetta, J.M., 2018. Quantification and characterization of
        leakage errors. Physical Review A, 97(3), p.032306.
    """
    n_qubits = 2
    d = 2**n_qubits

    L1 = 0  # leakage error
    if fit.leakage_fit is not None:
        L1 = (1 - fit.leakage_fit.A) * (1 - fit.leakage_fit.lambda_2)

    fidelity = (1 / d) * ((d - 1) * fit.ground_state_fit.lambda_2 + 1 - L1)

    return fidelity


def get_interleaved_gate_fidelity(num_qubits: int, reference_alpha: float, interleaved_alpha: float):
    """
    Calculates the interleaved gate fidelity using the formula from https://arxiv.org/pdf/1210.7011.

    Args:
        num_qubits (int): Number of qubits involved.
        reference_alpha (float): Decay constant from the reference RB experiment.
        interleaved_alpha (float): Decay constant from the interleaved RB experiment.

    Returns:
        float: Estimated interleaved gate fidelity.
    """
    return 1 - ((2**num_qubits - 1) * (1 - interleaved_alpha / reference_alpha) / 2**num_qubits)
