import json
import tempfile
import os
from pathlib import Path
from typing import Any

DEFAULTS = {
    "cats": [
        {"name": "大橘", "file": "orange_cat.gif", "builtin": True},
        {"name": "蓝猫", "file": "blue_cat.gif", "builtin": True},
        {"name": "三花", "file": "calico_cat.gif", "builtin": True},
    ],
    "active_cats": ["大橘", "蓝猫", "三花"],
    "cat_count": 2,
    "cat_size": 100,
    "work_interval_min": 50,
    "break_duration_min": 5,
    "idle_threshold_sec": 5,
    "dismiss_hide_min": 1,
    "sound_enabled": True,
    "sound_volume": 30,
    "custom_sounds": [],
    "auto_start": True,
    "first_run": True,
}

RANGES = {
    "cat_count": (1, 10),
    "cat_size": (30, 300),
    "work_interval_min": (15, 120),
    "break_duration_min": (1, 30),
    "idle_threshold_sec": (2, 30),
    "dismiss_hide_min": (1, 30),
    "sound_volume": (0, 100),
}


class ConfigStore:
    def __init__(self, filepath: Path):
        self._filepath = filepath
        self.settings: dict[str, Any] = dict(DEFAULTS)
        self._load()

    def _load(self):
        if not self._filepath.exists():
            return
        try:
            raw = json.loads(self._filepath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for key, default in DEFAULTS.items():
            val = raw.get(key)
            if val is not None and type(val) == type(default):
                if key in RANGES and isinstance(val, (int, float)):
                    lo, hi = RANGES[key]
                    if not (lo <= val <= hi):
                        continue
                self.settings[key] = val

    def save(self):
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        self._validate()
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._filepath.parent),
            prefix="config_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=True, indent=2)
            os.replace(tmp_path, self._filepath)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _validate(self):
        for key, (lo, hi) in RANGES.items():
            if key in self.settings and isinstance(self.settings[key], (int, float)):
                self.settings[key] = max(lo, min(hi, self.settings[key]))
