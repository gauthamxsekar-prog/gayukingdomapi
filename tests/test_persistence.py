import os
import sys
import tempfile
import importlib
from pathlib import Path


def test_data_dir_uses_project_root_regardless_of_cwd():
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    with tempfile.TemporaryDirectory() as temp_dir:
        previous_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            sys.modules.pop("main", None)
            main = importlib.import_module("main")
        finally:
            os.chdir(previous_cwd)

        expected_data_dir = (repo_root / "data").resolve()
        assert main.DATA_DIR.resolve() == expected_data_dir


def test_mongo_config_uses_mongodb_env_vars(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017/")
    monkeypatch.setenv("MONGODB_DB", "testdb")
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MONGO_DB", raising=False)

    sys.modules.pop("main", None)
    main = importlib.import_module("main")

    assert main.get_mongo_config() == ("mongodb://localhost:27017/", "testdb")


def test_mongo_config_defaults_to_localhost_when_env_missing(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("MONGODB_DB", raising=False)
    monkeypatch.delenv("MONGO_DB", raising=False)

    sys.modules.pop("main", None)
    main = importlib.import_module("main")

    assert main.get_mongo_config() == ("mongodb://localhost:27017/", "gayukingdomdb")
