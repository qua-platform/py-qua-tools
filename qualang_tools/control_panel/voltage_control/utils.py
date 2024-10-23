import numpy as np


def get_exponent(val: float) -> int:
    """Get decimal exponent of a value.

    Args:
        val: Value of which to get exponent

    Returns:
        Exponent

    Raises:
        ValueError: If val is less than or equal to zero
    """
    if val <= 0:
        raise ValueError(f"Value {val} must be larger than zero")
    return int(np.floor(np.log10(val)))


def get_first_digit(val: float) -> int:
    """Get first nonzero digit of a value.

    Args:
        val: Value for which to get first nonzero digit

    Returns:
        First nonzero digit
    """
    return int(np.floor(val * 10 ** -get_exponent(val)))
