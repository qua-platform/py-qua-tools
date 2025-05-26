import numpy as np


def module_installed(module_name):
    try:
        exec(f"import {module_name}")
    except ImportError:
        return False
    return True


def dicts_equal(d1, d2):
    import xarray as xr

    if d1.keys() != d2.keys():
        return False
    for key in d1:
        if key not in d2:
            return False
        elif isinstance(d1[key], dict):
            if not dicts_equal(d1[key], d2[key]):
                return False
        elif isinstance(d1[key], np.ndarray):
            if not np.array_equal(d1[key], d2[key]):
                return False
        elif isinstance(d1[key], xr.Dataset):
            if not d1[key].identical(d2[key]):
                return False
        else:
            if not bool(d1[key] == d2[key]):
                return False
    return True
