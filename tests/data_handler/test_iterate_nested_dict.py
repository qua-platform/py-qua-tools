from qualang_tools.results.data_handler.data_processors.helpers import iterate_nested_dict


def test_iterate_nested_dict_empty():
    d = {}

    result = list(iterate_nested_dict(d))
    assert result == []


def test_iterate_nested_dict_basic():
    d = {"a": 1, "b": 2, "c": 3}

    result = list(iterate_nested_dict(d))
    assert result == [(["a"], 1), (["b"], 2), (["c"], 3)]


def test_iterate_nested_dict_nested():
    d = {"a": 1, "b": {"c": 2, "d": 3}}

    result = list(iterate_nested_dict(d))
    assert result == [(["a"], 1), (["b"], d["b"]), (["b", "c"], 2), (["b", "d"], 3)]
