import re

import pytest
from packaging.version import Version

from qualang_tools.results.qua_iterables_processing import qua_iterable_postprocess as pp

_REQUIRED_ERROR = re.escape(f"qm-qua>={pp.MIN_QM_QUA_VERSION}")
# A version guaranteed to be below the minimum, derived from the constant.
_TOO_OLD = Version(f"{pp.MIN_QM_QUA_VERSION.major}.0.0")


@pytest.fixture
def simulate_old_qm_qua(monkeypatch):
    """Report an installed qm-qua older than the minimum required version."""
    monkeypatch.setattr(pp, "_installed_qm_qua_version", lambda: _TOO_OLD)


def test_qua_iterables_supported_version_gate(monkeypatch):
    monkeypatch.setattr(pp, "_installed_qm_qua_version", lambda: _TOO_OLD)
    assert pp.qua_iterables_supported() is False

    # Exactly the minimum is supported.
    monkeypatch.setattr(pp, "_installed_qm_qua_version", lambda: pp.MIN_QM_QUA_VERSION)
    assert pp.qua_iterables_supported() is True

    # A clearly newer version is supported.
    newer = Version(f"{pp.MIN_QM_QUA_VERSION.major + 1}.0.0")
    monkeypatch.setattr(pp, "_installed_qm_qua_version", lambda: newer)
    assert pp.qua_iterables_supported() is True


def test_import_helper_raises_clean_error(simulate_old_qm_qua):
    with pytest.raises(ImportError, match=_REQUIRED_ERROR):
        pp._import_qua_iterables_api()


def test_fetch_xarray_data_raises_clean_error(simulate_old_qm_qua):
    # The version guard runs before any job/iterables access, so dummy args are fine.
    with pytest.raises(ImportError, match=_REQUIRED_ERROR):
        pp.fetch_xarray_data(job=None, iterables=None)
