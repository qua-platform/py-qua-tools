from typing import Dict, Any, Generator, List, Tuple, Optional


def iterate_nested_dict(
    d: Dict[str, Any], parent_keys: Optional[List[str]] = None
) -> Generator[Tuple[List[str], Any], None, None]:
    """Iterate over a nested dictionary

    :param d: The dictionary to iterate over
    :param parent_keys: The keys of the parent dictionary. Used for recursion

    :return: A generator that yields a tuple of the keys and the value

    """
    if parent_keys is None:
        parent_keys = []
    for k, v in d.items():
        keys = parent_keys + [k]
        yield keys, v
        if isinstance(v, dict):
            yield from iterate_nested_dict(v, parent_keys=keys)


def update_nested_dict(d: dict, keys: List[Any], value: Any) -> None:
    """Update a nested dictionary with a new value

    :param d: The dictionary to update
    :param keys: The keys to the value to update
    :param value: The new value to set
    """
    subdict = d
    for key in keys[:-1]:
        subdict = subdict[key]

    subdict[keys[-1]] = value


def copy_nested_dict(d: dict) -> dict:
    """Copy a nested dictionary, but don't make copies of the values

    This function will copy a nested dictionary, but will not make copies of the values. This is useful if copying the
    values may be an expensive operation (e.g. large arrays).
    If you also want to make copies of the values, use `copy.deepcopy`

    :param d: The dictionary to copy
    :return: A new dictionary with the same structure as `d`, but with the same values
    """
    new_dict = {}
    for key, val in d.items():
        if isinstance(val, dict):
            new_dict[key] = copy_nested_dict(val)
        else:
            new_dict[key] = val
    return new_dict
