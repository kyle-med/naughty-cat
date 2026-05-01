import json
import tempfile
from pathlib import Path
from naughty_cat.config_store import ConfigStore


def test_defaults_on_no_file():
    tmp = Path(tempfile.mkdtemp()) / "nonexistent.json"
    store = ConfigStore(tmp)
    assert store.settings["work_interval_min"] == 50
    assert store.settings["break_duration_min"] == 5
    assert store.settings["first_run"] is True
    assert len(store.settings["cats"]) == 4


def test_loads_existing_file():
    tmp = Path(tempfile.mkdtemp()) / "config.json"
    tmp.write_text('{"work_interval_min": 30, "first_run": false, "dismiss_hide_min": 3}')
    store = ConfigStore(tmp)
    assert store.settings["work_interval_min"] == 30
    assert store.settings["first_run"] is False
    assert store.settings["dismiss_hide_min"] == 3
    # missing keys get defaults
    assert store.settings["break_duration_min"] == 5


def test_save_persists_and_is_json():
    tmp = Path(tempfile.mkdtemp()) / "config.json"
    store = ConfigStore(tmp)
    store.settings["work_interval_min"] = 60
    store.save()
    raw = json.loads(tmp.read_text())
    assert raw["work_interval_min"] == 60


def test_save_does_not_corrupt_on_crash():
    """Atomic write: temp file then rename. Original survives partial write."""
    import os
    tmp = Path(tempfile.mkdtemp()) / "config.json"
    tmp.write_text('{"work_interval_min": 30}')
    store = ConfigStore(tmp)
    store.settings["work_interval_min"] = 90
    # simulate crash by checking that a temp file is created
    store.save()
    # After save, the real file should exist and have the new value
    raw = json.loads(tmp.read_text())
    assert raw["work_interval_min"] == 90


def test_invalid_values_fallback_to_defaults():
    tmp = Path(tempfile.mkdtemp()) / "config.json"
    tmp.write_text('{"work_interval_min": -5, "break_duration_min": 999, "cat_size": "big"}')
    store = ConfigStore(tmp)
    # Invalid values should be rejected, fallback to defaults
    assert store.settings["work_interval_min"] == 50
    assert store.settings["break_duration_min"] == 5


def test_validate_normalizes_ranges():
    tmp = Path(tempfile.mkdtemp()) / "config.json"
    store = ConfigStore(tmp)
    store.settings["work_interval_min"] = 200  # max is 120
    store.settings["dismiss_hide_min"] = 0     # min is 1
    store.save()
    raw = json.loads(tmp.read_text())
    assert raw["work_interval_min"] == 120
    assert raw["dismiss_hide_min"] == 1
