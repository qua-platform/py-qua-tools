def import_cirq():
    try:
        import cirq

        return cirq
    except ImportError:
        raise ImportError(
            "Cirq is not installed. Please install it with:\n"
            "pip install cirq==1.2.0\n"
            "Note: Cirq requires Python >= 3.10. Please ensure your Python version meets this requirement."
        )
