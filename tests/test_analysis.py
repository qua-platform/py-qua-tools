import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from qualang_tools.analysis.discriminator import two_state_discriminator




def abs_path_to(rel_path: str) -> str:
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    return os.path.join(source_dir, rel_path)


def test_IQ_blobs_works():
    Ig, Ie, Qg, Qe = np.load(abs_path_to('IQblobs.npy'))
    angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(Ig, Qg, Ie, Qe)

    C = np.cos(angle)
    S = np.sin(angle)
    Ig_rotated = Ig * C - Qg * S
    Qg_rotated = Ig * S + Qg * C
    Ie_rotated = Ie * C - Qe * S
    Qe_rotated = Ie * S + Qe * C

    assert np.isclose(np.mean(Qg_rotated), np.mean(Qe_rotated))
    assert gg > 0.80
    assert ee > 0.80
    assert ge < 0.20
    assert eg < 0.20


def test_IQ_blobs_angle():
    Ig, Ie, Qg, Qe = np.load(abs_path_to('IQblobs.npy'))
    angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(Ig, Qg, Ie, Qe)
    C = np.cos(angle)
    S = np.sin(angle)
    Ig_rotated_results = Ig * C - Qg * S
    Qg_rotated_results = Ig * S + Qg * C
    Ie_rotated_results = Ie * C - Qe * S
    Qe_rotated_results = Ie * S + Qe * C
    assert np.mean(Ie_rotated_results) > np.mean(Ig_rotated_results)

    # Test again when data is rotated by pi
    angle = np.pi
    C = np.cos(angle)
    S = np.sin(angle)
    Ig_rotated_pi = Ig * C - Qg * S
    Qg_rotated_pi = Ig * S + Qg * C
    Ie_rotated_pi = Ie * C - Qe * S
    Qe_rotated_pi = Ie * S + Qe * C

    angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(Ig_rotated_pi, Qg_rotated_pi, Ie_rotated_pi, Qe_rotated_pi)
    C = np.cos(angle)
    S = np.sin(angle)
    Ig_rotated_results = Ig_rotated_pi * C - Qg_rotated_pi * S
    Qg_rotated_results = Ig_rotated_pi * S + Qg_rotated_pi * C
    Ie_rotated_results = Ie_rotated_pi * C - Qe_rotated_pi * S
    Qe_rotated_results = Ie_rotated_pi * S + Qe_rotated_pi * C
    assert np.mean(Ie_rotated_results) > np.mean(Ig_rotated_results)

