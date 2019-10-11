import pytest
from sklearn.base import BaseEstimator
from sklearn.pipeline import Pipeline

from ml_tooling import Model
from ml_tooling.storage import Storage
from ml_tooling.storage.file import FileStorage


def test_can_save_file(classifier, tmp_path):
    storage = FileStorage(tmp_path)
    expected_file = storage.save(classifier.estimator, "estimator")
    assert expected_file.exists()


def test_can_save_with_model(classifier, tmp_path):
    storage = FileStorage(tmp_path)
    expected_file = classifier.save_estimator(storage)
    assert expected_file.exists()

    with FileStorage(tmp_path) as storage_context:
        context_expected_file = classifier.save_estimator(storage_context)
        assert context_expected_file.exists()


def test_can_load_file(classifier, tmp_path):
    storage = FileStorage(tmp_path)
    storage.save(classifier.estimator, "estimator")
    loaded_file = storage.load(tmp_path / "estimator")
    assert isinstance(loaded_file, (BaseEstimator, Pipeline))


def test_can_load_with_model(classifier, tmp_path):
    storage = FileStorage(tmp_path)
    expected_file = classifier.save_estimator(storage)
    assert expected_file.exists()
    loaded_file = classifier.load_estimator(storage, expected_file)
    assert isinstance(loaded_file, Model)
    with FileStorage(tmp_path) as storage_context:
        context_loaded_file = classifier.load_estimator(storage_context, expected_file)
        assert isinstance(context_loaded_file, Model)


def test_can_list_estimators(classifier, tmp_path):
    storage = FileStorage(tmp_path)
    for _ in range(3):
        classifier.save_estimator(storage)
    with FileStorage(tmp_path) as storage_context:
        filenames_list = Model.list_estimators(storage_context)
        for filename in filenames_list:
            assert filename.exists()


def test_cannot_instantiate_an_abstract_baseclass():
    with pytest.raises(TypeError):
        Storage()