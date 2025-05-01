import numpy as np


def single_exponential_decay_model(m: np.ndarray, A: float, B: float, _lambda: float) -> np.ndarray:
    """
    Single-exponential decay model
        A + Bλᵐ.
    """
    return A + B * _lambda**m


def double_exponential_decay_model(
    m: np.ndarray, A: float, B: float, lambda_1: float, C: float, lambda_2: float
) -> np.ndarray:
    """
    Double-exponential decay model.
        A + Bλ₁ᵐ + Cλ₂ᵐ.
    """
    return A + B * lambda_1**m + C * lambda_2**m
