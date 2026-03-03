import importlib


def test_data_dir_default(monkeypatch):
    monkeypatch.delenv("GAMECOMPANION_DATA_DIR", raising=False)
    monkeypatch.delenv("GAMECOMPANION_TEST_MODE", raising=False)
    import gamecompanion.config as config
    importlib.reload(config)

    assert str(config.DATA_DIR) == "data"


def test_paths_derived_from_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("GAMECOMPANION_DATA_DIR", str(tmp_path))
    import gamecompanion.config as config
    importlib.reload(config)

    assert config.DB_PATH == tmp_path / "gamecompanion.db"
    assert config.CONFIG_PATH == tmp_path / "config.json"


def test_test_mode_flag(monkeypatch):
    monkeypatch.setenv("GAMECOMPANION_TEST_MODE", "1")
    import gamecompanion.config as config
    importlib.reload(config)
    assert config.TEST_MODE is True

    monkeypatch.setenv("GAMECOMPANION_TEST_MODE", "0")
    importlib.reload(config)
    assert config.TEST_MODE is False
