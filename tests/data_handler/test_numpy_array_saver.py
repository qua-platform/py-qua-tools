import numpy as np

from qualang_tools.results.data_handler.data_processors import DEFAULT_DATA_PROCESSORS, NumpyArraySaver


def test_numpy_array_saver_process_merged_below_min_size():
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver()
    processed_data = data.copy()
    processed_data = data_processor.process(processed_data)
    assert processed_data == data


def test_numpy_array_saver_process_merged():
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver(min_size=False)

    processed_data = data.copy()
    processed_data = data_processor.process(processed_data)

    assert processed_data == {
        "a": "./arrays.npz#a",
        "b": "./arrays.npz#b",
        "c": 3,
    }


def test_numpy_array_saver_process_separate():
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver(min_size=False)
    processed_data = data_processor.process(data)
    assert processed_data == {
        "a": "./arrays.npz#a",
        "b": "./arrays.npz#b",
        "c": 3,
    }


def test_numpy_array_saver_post_process_merged(tmp_path):
    data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6]), "c": 3}

    data_processor = NumpyArraySaver(min_size=False)

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

    data_processor = NumpyArraySaver(min_size=False, merge_arrays=False)
    data_processor.process(data.copy())

    data_processor.post_process(data_folder=tmp_path)

    assert (tmp_path / "a.npy").exists()
    assert (tmp_path / "b.npy").exists()
    assert np.array_equal(np.load(tmp_path / "a.npy"), data["a"])
    assert np.array_equal(np.load(tmp_path / "b.npy"), data["b"])
