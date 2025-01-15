import copy
import numpy as np

from qualang_tools.results.data_handler.data_processors import DEFAULT_DATA_PROCESSORS, NumpyArraySaver


def dicts_equal(d1, d2):
    if d1.keys() != d2.keys():
        return False
    for key in d1:
        if isinstance(d1[key], dict):
            if not dicts_equal(d1[key], d2[key]):
                return False
        elif isinstance(d1[key], np.ndarray) or isinstance(d2[key], np.ndarray):
            if not np.array_equal(d1[key], d2[key]):
                return False
        else:
            if d1[key] != d2[key]:
                return False
    return True


def test_numpy_array_saver_process_merged():
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver()

    processed_data = data_processor.process(data)

    assert processed_data == {
        "a": "./arrays.npz#a",
        "b": "./arrays.npz#b",
        "c": 3,
    }


def test_numpy_array_saver_process_separate():
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver()
    processed_data = data_processor.process(data)
    assert processed_data == {
        "a": "./arrays.npz#a",
        "b": "./arrays.npz#b",
        "c": 3,
    }


def test_numpy_array_saver_post_process_merged(tmp_path):
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver()

    processed_data = data.copy()
    data_processor.process(processed_data)

    data_processor.post_process(data_folder=tmp_path)

    assert (tmp_path / "arrays.npz").exists()
    loaded_data = np.load(tmp_path / "arrays.npz")
    assert list(loaded_data.keys()) == ["a", "b"]
    assert np.array_equal(loaded_data["a"], data["a"])
    assert np.array_equal(loaded_data["b"], data["b"])


def test_numpy_array_saver_post_process_separate(tmp_path):
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver(merge_arrays=False)
    data_processor.process(data)

    data_processor.post_process(data_folder=tmp_path)

    assert (tmp_path / "a.npy").exists()
    assert (tmp_path / "b.npy").exists()
    assert np.array_equal(np.load(tmp_path / "a.npy"), data["a"])
    assert np.array_equal(np.load(tmp_path / "b.npy"), data["b"])


def test_numpy_array_saver_nested_no_merge(tmp_path):
    data = {"q0": {"a": np.array([1, 2, 3]), "b": 3}, "c": np.array([4, 5, 6])}

    data_processor = NumpyArraySaver(merge_arrays=False)
    processed_data = data_processor.process(data)
    assert processed_data == {
        "q0": {"a": "./q0.a.npy", "b": 3},
        "c": "./c.npy",
    }

    data_processor.post_process(data_folder=tmp_path)

    assert (tmp_path / "q0.a.npy").exists()
    assert not (tmp_path / "q0.b.npy").exists()
    assert (tmp_path / "c.npy").exists()

    assert np.array_equal(np.load(tmp_path / "q0.a.npy"), data["q0"]["a"])
    assert np.array_equal(np.load(tmp_path / "c.npy"), data["c"])


def test_numpy_array_saver_process_does_not_affect_data():
    data = {"q0": {"a": np.array([1, 2, 3]), "b": 3}, "c": np.array([4, 5, 6])}
    deepcopied_data = copy.deepcopy(data)

    data_processor = NumpyArraySaver(merge_arrays=False)
    processed_data = data_processor.process(data)

    assert dicts_equal(data, deepcopied_data)
    assert not dicts_equal(processed_data, data)
