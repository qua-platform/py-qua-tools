import numpy as np
import pytest

from qualang_tools.loops import split_frequency_sweep


def test_raises_when_fmax_below_fmin():
    with pytest.raises(ValueError, match="fmax must be >= fmin"):
        split_frequency_sweep(2e9, 1e9, 1e6)


def test_raises_when_df_non_positive():
    with pytest.raises(ValueError, match="df must be positive"):
        split_frequency_sweep(1e9, 2e9, 0.0)
    with pytest.raises(ValueError, match="df must be positive"):
        split_frequency_sweep(1e9, 2e9, -1e6)


def test_raises_when_max_if_bandwidth_non_positive():
    with pytest.raises(ValueError, match="max_if_bandwidth must be positive"):
        split_frequency_sweep(1e9, 2e9, 1e6, max_if_bandwidth=0.0)


def test_raises_asymmetric_invalid_if_range():
    with pytest.raises(ValueError, match="if_min_hz must be non-negative"):
        split_frequency_sweep(1e9, 2e9, 1e6, symmetric_span=False, if_min_hz=-1.0)
    with pytest.raises(ValueError, match="max_if_bandwidth must be greater than if_min_hz"):
        split_frequency_sweep(
            1e9, 2e9, 1e6, symmetric_span=False, if_min_hz=100e6, max_if_bandwidth=100e6
        )


def test_single_rf_point():
    los, if_offsets, rf_freqs = split_frequency_sweep(1e9, 1e9, 1e6)
    assert los == [1e9]
    assert if_offsets == [0.0]
    assert np.array_equal(rf_freqs, np.array([1e9]))


def test_symmetric_reconstructs_rf_grid():
    fmin, fmax, df = 1.0e9, 1.0e9 + 10e6, 1e6
    max_if = 4e6
    los, if_offsets, rf_freqs = split_frequency_sweep(
        fmin, fmax, df, max_if_bandwidth=max_if, symmetric_span=True
    )
    n_if = len(if_offsets)
    for j in range(len(los)):
        for k in range(n_if):
            idx = j * n_if + k
            if idx < len(rf_freqs):
                assert np.isclose(los[j] + if_offsets[k], rf_freqs[idx])


def test_symmetric_lo_is_segment_midpoint():
    fmin, fmax, df = 5e9, 5e9 + 5e6, 1e6
    los, if_offsets, rf_freqs = split_frequency_sweep(
        fmin, fmax, df, max_if_bandwidth=3e6, symmetric_span=True
    )
    n_if = len(if_offsets)
    for j in range(len(los)):
        seg = rf_freqs[j * n_if : (j + 1) * n_if]
        assert np.isclose(los[j], (float(seg[0]) + float(seg[-1])) / 2.0)


def test_symmetric_extends_grid_past_fmax_when_needed():
    fmin, fmax, df = 1e9, 1e9 + 5e6, 1e6
    los, if_offsets, rf_freqs = split_frequency_sweep(
        fmin, fmax, df, max_if_bandwidth=3e6, symmetric_span=True
    )
    n_original = int(np.floor((fmax - fmin) / df + 1e-12)) + 1
    assert len(rf_freqs) >= n_original
    assert np.isclose(rf_freqs[0], fmin)
    for i in range(len(rf_freqs)):
        assert np.isclose(rf_freqs[i], fmin + i * df)


def test_symmetric_if_span_respects_max_bandwidth():
    df = 1e6
    max_if = 10e6
    _, if_offsets, _ = split_frequency_sweep(
        1e9, 2e9, df, max_if_bandwidth=max_if, symmetric_span=True
    )
    span = (len(if_offsets) - 1) * df
    assert span <= max_if + 1e-9


def test_asymmetric_reconstructs_rf_grid():
    fmin, fmax, df = 2.0e9, 2.0e9 + 8e6, 1e6
    if_min = 1e6
    max_if = 5e6
    los, if_offsets, rf_freqs = split_frequency_sweep(
        fmin, fmax, df, max_if_bandwidth=max_if, symmetric_span=False, if_min_hz=if_min
    )
    n_if = len(if_offsets)
    for j in range(len(los)):
        for k in range(n_if):
            idx = j * n_if + k
            if idx < len(rf_freqs):
                assert np.isclose(los[j] + if_offsets[k], rf_freqs[idx])


def test_asymmetric_if_offsets_template():
    df = 0.5e6
    if_min = 2e6
    max_if = 10e6
    _, if_offsets, _ = split_frequency_sweep(
        1e9, 1.1e9, df, max_if_bandwidth=max_if, symmetric_span=False, if_min_hz=if_min
    )
    expected = [if_min + k * df for k in range(len(if_offsets))]
    assert np.allclose(if_offsets, expected)
