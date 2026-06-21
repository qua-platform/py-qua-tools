import builtins

import pytest

from qualang_tools.results.qua_iterables_processing import qua_iterable_postprocess as pp


@pytest.fixture
def simulate_old_qm_qua(monkeypatch):
    """Make the qm-qua 1.3.1 symbols look unavailable, as on qm-qua<1.3.1."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "qm.qua.extensions.qua_iterators" or (
            name == "qm.qua" and "STREAM_NAME_SEPARATOR" in (args[2] or ())
        ):
            raise ImportError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_import_helper_raises_clean_error(simulate_old_qm_qua):
    with pytest.raises(ImportError, match="qm-qua>=1.3.1"):
        pp._import_qua_iterables_api()


def test_fetch_xarray_data_raises_clean_error(simulate_old_qm_qua):
    # The version guard runs before any job/iterables access, so dummy args are fine.
    with pytest.raises(ImportError, match="qm-qua>=1.3.1"):
        pp.fetch_xarray_data(job=None, iterables=None)


def test_module_imports_without_qua_iterators(simulate_old_qm_qua):
    """Importing the package must not require the qm-qua 1.3.1 symbols."""
    import importlib

    importlib.reload(pp)
    assert hasattr(pp, "fetch_xarray_data")
