from unittest.mock import MagicMock

import pytest
from qm import QopCaps

from qualang_tools.multi_user import qm_session


def test_qm_session_timeout_must_be_positive():
    with pytest.raises(ValueError, match="must be positive"):
        with qm_session(MagicMock(), {}, timeout=0):
            pass


def test_qm_session_busy_times_out_with_mock_qmm():
    qmm = MagicMock()
    qmm.capabilities.supports.return_value = False
    qmm.open_qm.side_effect = Exception("cannot be used because it isn't shareable in other QM.")

    with pytest.raises(TimeoutError, match="timeout"):
        with qm_session(qmm, {"controllers": {}}, timeout=0.3):
            pass


def test_qm_session_unexpected_open_error_is_reraised():
    qmm = MagicMock()
    qmm.capabilities.supports.return_value = False
    qmm.open_qm.side_effect = Exception("unrelated failure")

    with pytest.raises(Exception) as exc_info:
        with qm_session(qmm, {"controllers": {}}, timeout=1):
            pass
    assert "unrelated failure" in str(exc_info.value.__cause__)


def test_qm_session_busy_qop3_message():
    qmm = MagicMock()
    qmm.capabilities.supports.side_effect = lambda cap: cap == QopCaps.qop3
    qmm.open_qm.side_effect = Exception("Resources already locked")

    with pytest.raises(TimeoutError):
        with qm_session(qmm, {"controllers": {}}, timeout=0.3):
            pass
