from typing import Any, Dict


__all__ = ["dicts_equal"]


def dicts_equal(d1: Dict[Any, Any], d2: Dict[Any, Any]) -> bool:
    """Check if two dictionaries are equal.

    This method checks if two dictionaries are equal by comparing their keys and values recursively.
    """
    if d1.keys() != d2.keys():
        return False
    for key, value in d1.items():
        if isinstance(value, dict):
            if not dicts_equal(value, d2[key]):
                return False
        elif isinstance(value, list):
            if not isinstance(d2[key], list) or len(value) != len(d2[key]):
                return False
            for v1, v2 in zip(value, d2[key]):
                if isinstance(v1, dict):
                    if not dicts_equal(v1, v2):
                        return False
                elif v1 != v2:
                    return False
        elif value != d2[key]:
            return False
    return True
