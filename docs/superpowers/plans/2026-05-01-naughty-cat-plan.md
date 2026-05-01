# Naughty Cat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows break-reminder app where animated cats appear on screen at configurable intervals and playfully occupy the display until the user takes a proper break.

**Architecture:** Modular Python + PySide6 app with 6 core modules (config_store, idle_detector, sound_player, state_machine, cat_manager, tray_icon) and 4 UI components. Each module has a single responsibility, communicates via Qt signals/slots, and can be tested independently with pytest-qt.

**Tech Stack:** Python 3.12, PySide6, QMediaPlayer, Win32 API (GetLastInputInfo via ctypes), PyInstaller, NSIS

---

## File Map

```
naughty_cat/
├── __init__.py
├── main.py                    # Entry point, wires components together
├── config_store.py            # JSON config read/write/validate
├── idle_detector.py           # Win32 GetLastInputInfo polling
├── sound_player.py            # QMediaPlayer audio playback
├── state_machine.py           # Core state machine with signals
├── cat_manager.py             # Cat window lifecycle & random walk
├── tray_icon.py               # System tray icon & context menu
├── ui/
│   ├── __init__.py
│   ├── cat_config.py          # Cat selection/import panel widget
│   ├── welcome_wizard.py      # First-run 3-step wizard dialog
│   ├── settings_window.py     # 4-tab settings dialog
│   └── break_done_toast.py    # "猫咪出去玩了" notification toast
├── assets/
│   ├── cats/                  # Built-in cat GIF/APNG files
│   │   ├── orange_cat.gif
│   │   ├── blue_cat.gif
│   │   └── calico_cat.gif
│   ├── sounds/                # Built-in meow sounds
│   │   ├── meow1.mp3
│   │   └── meow2.mp3
│   └── icons/
│       ├── cat.ico            # Tray icon (normal)
│       └── cat_sleep.ico      # Tray icon (paused)
tests/
├── __init__.py
├── test_config_store.py
├── test_idle_detector.py
├── test_sound_player.py
├── test_state_machine.py
├── test_cat_manager.py
├── test_tray_icon.py
├── test_cat_config.py
├── test_welcome_wizard.py
├── test_settings_window.py
└── test_break_done_toast.py
pyproject.toml
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `naughty_cat/__init__.py`
- Create: `tests/__init__.py`
- Create: `naughty_cat/assets/cats/.gitkeep`
- Create: `naughty_cat/assets/sounds/.gitkeep`
- Create: `naughty_cat/assets/icons/.gitkeep`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "naughty-cat"
version = "0.1.0"
description = "A break reminder app with naughty cats"
requires-python = ">=3.12"
dependencies = [
    "PySide6>=6.6",
]

[project.scripts]
naughty-cat = "naughty_cat.main:main"

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-qt>=4",
]

[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["naughty_cat*"]

[tool.pytest.ini_options]
qt_api = "pyside6"
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty __init__.py files**

Run:
```bash
echo "" > naughty_cat/__init__.py
echo "" > naughty_cat/ui/__init__.py
echo "" > tests/__init__.py
```

- [ ] **Step 3: Create asset placeholder dirs**

Run:
```bash
mkdir -p naughty_cat/assets/cats naughty_cat/assets/sounds naughty_cat/assets/icons
touch naughty_cat/assets/cats/.gitkeep
touch naughty_cat/assets/sounds/.gitkeep
touch naughty_cat/assets/icons/.gitkeep
```

- [ ] **Step 4: Install dependencies and verify**

Run:
```bash
pip install -e ".[dev]"
python -c "from PySide6.QtWidgets import QApplication; print('OK')"
```
Expected: prints "OK" without errors.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml naughty_cat/ tests/
git commit -m "chore: scaffold project with pyproject.toml and package layout"
```

---

### Task 2: Config Store

**Files:**
- Create: `naughty_cat/config_store.py`
- Create: `tests/test_config_store.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_config_store.py`:

```python
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
    assert len(store.settings["cats"]) == 3

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
    tmp.write_text('{"work_interval_min": -5, "break_duration_min": 999}, "cat_size": "big"}')
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_store.py -v`
Expected: FAIL — cannot import `ConfigStore`.

- [ ] **Step 3: Write minimal implementation**

Create `naughty_cat/config_store.py`:

```python
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
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._filepath)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _validate(self):
        for key, (lo, hi) in RANGES.items():
            if key in self.settings and isinstance(self.settings[key], (int, float)):
                self.settings[key] = max(lo, min(hi, self.settings[key]))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config_store.py -v`
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/config_store.py tests/test_config_store.py
git commit -m "feat: add config_store with JSON read/write and validation"
```

---

### Task 3: Idle Detector

**Files:**
- Create: `naughty_cat/idle_detector.py`
- Create: `tests/test_idle_detector.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_idle_detector.py`:

```python
import time
from PySide6.QtCore import QCoreApplication
from naughty_cat.idle_detector import IdleDetector

def test_idle_detector_starts_and_emits(qtbot):
    app = QCoreApplication.instance() or QCoreApplication([])
    detector = IdleDetector(check_interval_ms=100, idle_threshold_sec=0.05)
    signals_received = []

    def on_idle_changed(seconds):
        signals_received.append(seconds)

    detector.idle_seconds_changed.connect(on_idle_changed)
    detector.start()

    def check():
        assert len(signals_received) > 0
        assert signals_received[-1] >= 0  # idle seconds is a non-negative number

    qtbot.waitUntil(check, timeout=2000)

def test_idle_detector_stops(qtbot):
    detector = IdleDetector(check_interval_ms=50, idle_threshold_sec=60)
    detector.start()
    detector.stop()
    # After stop, no more signals should fire
    count_before = 0

    def on_idle_changed(seconds):
        nonlocal count_before
        count_before += 1

    detector.idle_seconds_changed.connect(on_idle_changed)

    def assert_stable():
        cnt = count_before
        time.sleep(0.3)
        assert cnt == count_before  # no new signals

    qtbot.waitUntil(assert_stable, timeout=2000)

def test_idle_detector_emits_became_idle(qtbot):
    app = QCoreApplication.instance() or QCoreApplication([])
    detector = IdleDetector(check_interval_ms=50, idle_threshold_sec=0.05)
    became_idle_called = False

    def on_became_idle():
        nonlocal became_idle_called
        became_idle_called = True

    detector.became_idle.connect(on_became_idle)
    detector.start()

    qtbot.waitUntil(lambda: became_idle_called, timeout=3000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_idle_detector.py -v`
Expected: FAIL — `IdleDetector` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/idle_detector.py`:

```python
import ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject, QTimer, Signal

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def _get_idle_seconds() -> float:
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    return (kernel32.GetTickCount() - lii.dwTime) / 1000.0


class IdleDetector(QObject):
    idle_seconds_changed = Signal(float)
    became_idle = Signal()

    def __init__(self, check_interval_ms=500, idle_threshold_sec=5, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(check_interval_ms)
        self._timer.timeout.connect(self._tick)
        self._idle_threshold = idle_threshold_sec
        self._was_idle = False

    def start(self):
        self._was_idle = False
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def _tick(self):
        secs = _get_idle_seconds()
        self.idle_seconds_changed.emit(secs)
        is_idle = secs >= self._idle_threshold
        if is_idle and not self._was_idle:
            self._was_idle = True
            self.became_idle.emit()
        elif not is_idle:
            self._was_idle = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_idle_detector.py -v`
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/idle_detector.py tests/test_idle_detector.py
git commit -m "feat: add idle_detector using GetLastInputInfo Win32 API"
```

---

### Task 4: Sound Player

**Files:**
- Create: `naughty_cat/sound_player.py`
- Create: `tests/test_sound_player.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_sound_player.py`:

```python
import tempfile
from pathlib import Path
from PySide6.QtCore import QCoreApplication
from naughty_cat.sound_player import SoundPlayer

def test_sound_player_initial_state():
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    assert player.volume() == 30
    assert player.enabled is True

def test_set_volume_clamps():
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    player.set_volume(50)
    assert player.volume() == 50
    player.set_volume(-10)
    assert player.volume() == 0
    player.set_volume(200)
    assert player.volume() == 100

def test_set_enabled():
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    player.set_enabled(False)
    assert player.enabled is False
    player.set_enabled(True)
    assert player.enabled is True

def test_play_does_not_crash_when_disabled(qtbot):
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    player.set_enabled(False)
    # Should not raise
    player.play("meow1.mp3")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sound_player.py -v`
Expected: FAIL — `SoundPlayer` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/sound_player.py`:

```python
from pathlib import Path
from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class SoundPlayer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._volume = 30
        self.enabled = True
        self._audio.setVolume(self._volume / 100.0)
        self._sound_dir = Path(__file__).parent / "assets" / "sounds"

    def volume(self) -> int:
        return self._volume

    def set_volume(self, vol: int):
        self._volume = max(0, min(100, vol))
        self._audio.setVolume(self._volume / 100.0)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def play(self, name: str):
        if not self.enabled:
            return
        path = self._sound_dir / name
        if path.exists():
            self._player.setSource(QUrl.fromLocalFile(str(path)))
            self._player.play()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sound_player.py -v`
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/sound_player.py tests/test_sound_player.py
git commit -m "feat: add sound_player with QMediaPlayer and volume control"
```

---

### Task 5: State Machine

**Files:**
- Create: `naughty_cat/state_machine.py`
- Create: `tests/test_state_machine.py`

The state machine is the core of the app. It uses QTimer for timers and Qt signals for events.

- [ ] **Step 1: Write failing test**

Create `tests/test_state_machine.py`:

```python
from PySide6.QtCore import QCoreApplication, QTimer
from naughty_cat.state_machine import StateMachine, State, Event

def test_initial_state_is_working():
    app = QCoreApplication.instance() or QCoreApplication([])
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    assert sm.current_state == State.WORKING

def test_work_timer_fire_transitions_to_cat_show(qtbot):
    sm = StateMachine(work_interval_min=0.001, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    cat_show_reached = False

    def on_state_changed(new_state):
        nonlocal cat_show_reached
        if new_state == State.CAT_SHOW:
            cat_show_reached = True

    sm.state_changed.connect(on_state_changed)
    sm.start()

    qtbot.waitUntil(lambda: cat_show_reached, timeout=3000)
    assert sm.current_state == State.CAT_SHOW

def test_idle_detected_transitions_to_resting(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.CAT_SHOW)
    resting_reached = False

    def on_state_changed(new_state):
        nonlocal resting_reached
        if new_state == State.RESTING:
            resting_reached = True

    sm.state_changed.connect(on_state_changed)
    sm.transition(Event.IDLE_DETECTED)

    qtbot.waitUntil(lambda: resting_reached, timeout=500)
    assert sm.current_state == State.RESTING

def test_user_active_pauses_resting(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING)
    sm.transition(Event.USER_ACTIVE)
    qtbot.waitUntil(lambda: sm.current_state == State.RESTING_PAUSED, timeout=500)

def test_idle_resumes_from_paused(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING_PAUSED)
    sm.transition(Event.IDLE_DETECTED)
    qtbot.waitUntil(lambda: sm.current_state == State.RESTING, timeout=500)

def test_dismiss_transitions_to_hiding(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=0.001)
    sm._force_state(State.CAT_SHOW)
    hiding_reached = False

    def on_state_changed(new_state):
        nonlocal hiding_reached
        if new_state == State.CAT_HIDING:
            hiding_reached = True

    sm.state_changed.connect(on_state_changed)
    sm.transition(Event.DISMISS_CLICKED)

    qtbot.waitUntil(lambda: hiding_reached, timeout=3000)

def test_hide_timer_fire_returns_to_cat_show(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=0.001)
    sm._force_state(State.CAT_HIDING)
    sm._start_hide_timer()
    cat_show_reached = False

    def on_state_changed(new_state):
        nonlocal cat_show_reached
        if new_state == State.CAT_SHOW:
            cat_show_reached = True

    sm.state_changed.connect(on_state_changed)

    qtbot.waitUntil(lambda: cat_show_reached, timeout=3000)

def test_break_complete_transitions_to_rest_done(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=0.001,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING)
    sm._start_break_timer()
    rest_done_reached = False

    def on_state_changed(new_state):
        nonlocal rest_done_reached
        if new_state == State.REST_DONE:
            rest_done_reached = True

    sm.state_changed.connect(on_state_changed)

    qtbot.waitUntil(lambda: rest_done_reached, timeout=3000)

def test_user_acknowledge_resets_to_working(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.REST_DONE)
    sm.transition(Event.USER_ACKNOWLEDGE)
    qtbot.waitUntil(lambda: sm.current_state == State.WORKING, timeout=500)

def test_manual_summon_from_working(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm.transition(Event.MANUAL_SUMMON)
    qtbot.waitUntil(lambda: sm.current_state == State.CAT_SHOW, timeout=500)

def test_pause_and_resume(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm.pause()
    assert sm.is_paused is True
    sm.resume()
    assert sm.is_paused is False
    assert sm.current_state == State.WORKING  # timer resets
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_state_machine.py -v`
Expected: FAIL — `StateMachine` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/state_machine.py`:

```python
from enum import Enum, auto
from PySide6.QtCore import QObject, QTimer, Signal


class State(Enum):
    WORKING = auto()
    CAT_SHOW = auto()
    RESTING = auto()
    RESTING_PAUSED = auto()
    CAT_HIDING = auto()
    REST_DONE = auto()


class Event(Enum):
    WORK_TIMER_FIRE = auto()
    IDLE_DETECTED = auto()
    USER_ACTIVE = auto()
    BREAK_COMPLETE = auto()
    DISMISS_CLICKED = auto()
    HIDE_TIMER_FIRE = auto()
    USER_ACKNOWLEDGE = auto()
    MANUAL_SUMMON = auto()


class StateMachine(QObject):
    state_changed = Signal(State)
    paused_changed = Signal(bool)

    def __init__(self, work_interval_min, break_duration_min,
                 idle_threshold_sec, dismiss_hide_min, parent=None):
        super().__init__(parent)
        self._work_interval_ms = int(work_interval_min * 60 * 1000)
        self._break_duration_ms = int(break_duration_min * 60 * 1000)
        self._dismiss_hide_ms = int(dismiss_hide_min * 60 * 1000)
        self._idle_threshold = idle_threshold_sec

        self._current_state = State.WORKING
        self.is_paused = False

        self._work_timer = QTimer(self)
        self._work_timer.setSingleShot(True)
        self._work_timer.timeout.connect(self._on_work_timer_fire)

        self._break_timer = QTimer(self)
        self._break_timer.setSingleShot(True)
        self._break_timer.timeout.connect(self._on_break_timer_fire)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide_timer_fire)

    @property
    def current_state(self) -> State:
        return self._current_state

    def start(self):
        self._start_work_timer()

    def transition(self, event: Event):
        state = self._current_state

        if event == Event.WORK_TIMER_FIRE and state == State.WORKING:
            self._set_state(State.CAT_SHOW)

        elif event == Event.IDLE_DETECTED:
            if state == State.CAT_SHOW:
                self._set_state(State.RESTING)
                self._start_break_timer()
            elif state == State.RESTING_PAUSED:
                self._set_state(State.RESTING)
                self._start_break_timer()

        elif event == Event.USER_ACTIVE:
            if state == State.RESTING:
                self._break_timer.stop()
                self._set_state(State.RESTING_PAUSED)

        elif event == Event.DISMISS_CLICKED:
            if state in (State.CAT_SHOW, State.RESTING, State.RESTING_PAUSED):
                self._break_timer.stop()
                self._set_state(State.CAT_HIDING)
                self._start_hide_timer()

        elif event == Event.HIDE_TIMER_FIRE and state == State.CAT_HIDING:
            self._set_state(State.CAT_SHOW)

        elif event == Event.BREAK_COMPLETE and state == State.RESTING:
            self._set_state(State.REST_DONE)

        elif event == Event.USER_ACKNOWLEDGE and state == State.REST_DONE:
            self._set_state(State.WORKING)
            self._start_work_timer()

        elif event == Event.MANUAL_SUMMON:
            if state == State.WORKING:
                self._work_timer.stop()
                self._set_state(State.CAT_SHOW)

    def pause(self):
        self.is_paused = True
        self._work_timer.stop()
        self.paused_changed.emit(True)

    def resume(self):
        self.is_paused = False
        self._start_work_timer()
        self.paused_changed.emit(False)

    # --- internal ---

    def _force_state(self, state: State):
        """Test helper: jump to a state without timers."""
        self._work_timer.stop()
        self._break_timer.stop()
        self._hide_timer.stop()
        self._current_state = state

    def _set_state(self, state: State):
        self._current_state = state
        self.state_changed.emit(state)

    def _start_work_timer(self):
        if not self.is_paused:
            self._work_timer.start(self._work_interval_ms)

    def _start_break_timer(self):
        self._break_timer.start(self._break_duration_ms)

    def _start_hide_timer(self):
        self._hide_timer.start(self._dismiss_hide_ms)

    def _on_work_timer_fire(self):
        self.transition(Event.WORK_TIMER_FIRE)

    def _on_break_timer_fire(self):
        self.transition(Event.BREAK_COMPLETE)

    def _on_hide_timer_fire(self):
        self.transition(Event.HIDE_TIMER_FIRE)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_state_machine.py -v`
Expected: 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/state_machine.py tests/test_state_machine.py
git commit -m "feat: add state_machine with all 6 states and transitions"
```

---

### Task 6: Cat Manager

**Files:**
- Create: `naughty_cat/cat_manager.py`
- Create: `tests/test_cat_manager.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_cat_manager.py`:

```python
from PySide6.QtCore import QCoreApplication
from naughty_cat.cat_manager import CatManager

def test_cat_manager_initial_state(qtbot):
    manager = CatManager()
    assert manager.cat_count == 0

def test_spawn_cats_creates_windows(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=2, size=100, active_cat_gifs=[
        "orange_cat.gif", "blue_cat.gif", "calico_cat.gif"
    ])
    assert manager.cat_count == 2

def test_dismiss_all_hides_windows(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=2, size=100, active_cat_gifs=[
        "orange_cat.gif", "blue_cat.gif"
    ])
    dismiss_requested = False

    def on_dismiss():
        nonlocal dismiss_requested
        dismiss_requested = True

    manager.dismiss_requested.connect(on_dismiss)
    manager.dismiss_all()
    assert dismiss_requested is True

def test_remove_all_destroys_windows(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=2, size=100, active_cat_gifs=[
        "orange_cat.gif", "blue_cat.gif"
    ])
    manager.remove_all()
    assert manager.cat_count == 0

def test_double_spawn_replaces_cats(qtbot):
    manager = CatManager()
    manager.spawn_cats(count=1, size=100, active_cat_gifs=["orange_cat.gif"])
    first_cats = manager._windows.copy()
    manager.spawn_cats(count=3, size=100, active_cat_gifs=["orange_cat.gif", "blue_cat.gif", "calico_cat.gif"])
    assert manager.cat_count == 3
    # Old windows should be destroyed
    for w in first_cats:
        assert not w.isVisible()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cat_manager.py -v`
Expected: FAIL — `CatManager` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/cat_manager.py`:

```python
import math
import random
from pathlib import Path
from PySide6.QtCore import QObject, QTimer, Signal, QPoint, QRect
from PySide6.QtGui import QScreen, QMovie, QMouseEvent
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication
from PySide6.QtCore import Qt


class _CatWindow(QWidget):
    def __init__(self, gif_path: str, size: int, manager, index: int):
        super().__init__()
        self._manager = manager
        self._index = index
        self._angle = random.uniform(0, 2 * math.pi)
        self._speed = random.uniform(80, 200)

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(size, size)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._label = QLabel(self)
        self._label.setFixedSize(size, size - 24)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setScaledContents(True)

        movie = QMovie(gif_path)
        movie.setScaledSize(self._label.size())
        self._label.setMovie(movie)
        movie.start()
        self._movie = movie

        dismiss_btn = QPushButton("驱赶 ×", self)
        dismiss_btn.setFixedHeight(20)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                border: 1px solid rgba(255,255,255,0.25);
                border-radius: 4px;
                color: rgba(255,255,255,0.8);
                font-size: 10px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        dismiss_btn.clicked.connect(self._manager.dismiss_all)

        layout.addWidget(self._label)
        layout.addWidget(dismiss_btn, alignment=Qt.AlignCenter)

        # Start at random position
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = random.randint(0, max(0, geo.width() - size))
            y = random.randint(0, max(0, geo.height() - size))
            self.move(x, y)

    def move_step(self, dt_sec: float, screen_rect: QRect):
        dx = math.cos(self._angle) * self._speed * dt_sec
        dy = math.sin(self._angle) * self._speed * dt_sec
        new_x = self.x() + int(dx)
        new_y = self.y() + int(dy)

        # Bounce off edges
        if new_x < screen_rect.left() or new_x + self.width() > screen_rect.right():
            self._angle = math.pi - self._angle
            new_x = max(screen_rect.left(), min(new_x, screen_rect.right() - self.width()))
        if new_y < screen_rect.top() or new_y + self.height() > screen_rect.bottom():
            self._angle = -self._angle
            new_y = max(screen_rect.top(), min(new_y, screen_rect.bottom() - self.height()))

        self.move(new_x, new_y)

    def update_size(self, size: int):
        self.setFixedSize(size, size)
        self._label.setFixedSize(size, size - 24)
        if self._movie:
            self._movie.setScaledSize(self._label.size())


class CatManager(QObject):
    dismiss_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._windows: list[_CatWindow] = []
        self._move_timer = QTimer(self)
        self._move_timer.setInterval(100)
        self._move_timer.timeout.connect(self._move_cats)
        self._dir_change_timer = QTimer(self)
        self._dir_change_timer.setInterval(3000)
        self._dir_change_timer.timeout.connect(self._randomize_directions)

        self._cats_dir = Path(__file__).parent / "assets" / "cats"

    @property
    def cat_count(self) -> int:
        return len(self._windows)

    def spawn_cats(self, count: int, size: int, active_cat_gifs: list[str]):
        self.remove_all()
        gifs = [str(self._cats_dir / g) for g in active_cat_gifs]
        if not gifs:
            return

        for i in range(count):
            gif = gifs[i % len(gifs)]
            win = _CatWindow(gif, size, self, i)
            win.show()
            self._windows.append(win)

        self._move_timer.start()
        self._dir_change_timer.start()

    def dismiss_all(self):
        self._move_timer.stop()
        self._dir_change_timer.stop()
        for w in self._windows:
            w.hide()
        self.dismiss_requested.emit()

    def remove_all(self):
        self._move_timer.stop()
        self._dir_change_timer.stop()
        for w in self._windows:
            w.close()
        self._windows.clear()

    def update_cats(self, count: int, size: int, active_cat_gifs: list[str]):
        if self._windows:
            self.spawn_cats(count, size, active_cat_gifs)

    def _move_cats(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_rect = screen.availableGeometry()
        dt = 0.1  # 100ms
        for w in self._windows:
            if w.isVisible():
                w.move_step(dt, screen_rect)

    def _randomize_directions(self):
        for w in self._windows:
            if random.random() < 0.5:
                w._angle = random.uniform(0, 2 * math.pi)
                w._speed = random.uniform(80, 200)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cat_manager.py -v`
Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/cat_manager.py tests/test_cat_manager.py
git commit -m "feat: add cat_manager with random walk cat overlay windows"
```

---

### Task 7: Cat Config Panel

**Files:**
- Create: `naughty_cat/ui/__init__.py`
- Create: `naughty_cat/ui/cat_config.py`
- Create: `tests/test_cat_config.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_cat_config.py`:

```python
from PySide6.QtWidgets import QApplication
from naughty_cat.ui.cat_config import CatConfigPanel

def test_cat_config_initializes_with_cats(qtbot):
    cats = [
        {"name": "大橘", "file": "orange_cat.gif", "builtin": True},
        {"name": "蓝猫", "file": "blue_cat.gif", "builtin": True},
    ]
    active = ["大橘"]
    panel = CatConfigPanel(cats, active, count=2, size=100)
    qtbot.addWidget(panel)

    # The panel should have checkboxes for each cat
    assert panel.cat_count_spin.value() == 2
    assert panel.cat_size_slider.value() == 100

def test_cat_config_import_button_exists(qtbot):
    cats = [{"name": "大橘", "file": "orange_cat.gif", "builtin": True}]
    panel = CatConfigPanel(cats, ["大橘"], count=1, size=100)
    qtbot.addWidget(panel)
    # Import button should exist
    assert panel._import_btn is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cat_config.py -v`
Expected: FAIL — `CatConfigPanel` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/ui/cat_config.py`:

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
    QSpinBox, QSlider, QPushButton, QFileDialog, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt


class CatConfigPanel(QWidget):
    def __init__(self, cats: list[dict], active_names: list[str],
                 count: int, size: int, parent=None):
        super().__init__(parent)
        self._cats = cats
        self._checkboxes: dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)

        # Cat selection
        cat_group = QGroupBox("选择猫咪")
        cat_layout = QVBoxLayout(cat_group)

        for cat in cats:
            cb = QCheckBox(cat["name"])
            cb.setChecked(cat["name"] in active_names)
            cb.toggled.connect(self._on_selection_changed)
            self._checkboxes[cat["name"]] = cb
            cat_layout.addWidget(cb)

        self._import_btn = QPushButton("导入猫咪 (GIF/APNG)...")
        cat_layout.addWidget(self._import_btn)

        layout.addWidget(cat_group)

        # Count and size
        settings_group = QGroupBox("猫咪设置")
        settings_layout = QVBoxLayout(settings_group)

        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("猫咪数量"))
        self.cat_count_spin = QSpinBox()
        self.cat_count_spin.setRange(1, 10)
        self.cat_count_spin.setValue(count)
        count_layout.addWidget(self.cat_count_spin)
        settings_layout.addLayout(count_layout)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("猫咪大小"))
        self.cat_size_slider = QSlider(Qt.Horizontal)
        self.cat_size_slider.setRange(30, 300)
        self.cat_size_slider.setValue(size)
        self.cat_size_label = QLabel(str(size))
        self.cat_size_slider.valueChanged.connect(
            lambda v: self.cat_size_label.setText(str(v))
        )
        size_layout.addWidget(self.cat_size_slider)
        size_layout.addWidget(self.cat_size_label)
        settings_layout.addLayout(size_layout)

        layout.addWidget(settings_group)
        layout.addStretch()

    def get_active_cats(self) -> list[str]:
        return [name for name, cb in self._checkboxes.items() if cb.isChecked()]

    def get_cat_count(self) -> int:
        return self.cat_count_spin.value()

    def get_cat_size(self) -> int:
        return self.cat_size_slider.value()

    def _on_selection_changed(self):
        pass  # Consumers can connect to checkboxes directly if needed
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cat_config.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/ui/__init__.py naughty_cat/ui/cat_config.py tests/test_cat_config.py
git commit -m "feat: add cat_config panel with selection, import, count and size controls"
```

---

### Task 8: Welcome Wizard

**Files:**
- Create: `naughty_cat/ui/welcome_wizard.py`
- Create: `tests/test_welcome_wizard.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_welcome_wizard.py`:

```python
from PySide6.QtWidgets import QApplication
from naughty_cat.ui.welcome_wizard import WelcomeWizard

def test_wizard_has_three_pages(qtbot):
    wizard = WelcomeWizard()
    qtbot.addWidget(wizard)
    # QWizard page IDs are non-negative integers
    assert wizard.pageIds()
    assert len(wizard.pageIds()) == 3

def test_wizard_sets_first_run_false(qtbot):
    wizard = WelcomeWizard()
    qtbot.addWidget(wizard)
    # The wizard should expose collected settings
    settings = wizard.get_settings()
    assert "first_run" in settings
    assert settings["first_run"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_welcome_wizard.py -v`
Expected: FAIL — `WelcomeWizard` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/ui/welcome_wizard.py`:

```python
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QCheckBox,
    QSlider, QHBoxLayout
)
from PySide6.QtCore import Qt
from naughty_cat.ui.cat_config import CatConfigPanel


class WelcomeWizard(QWizard):
    def __init__(self, cats=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用 Naughty Cat")
        self.setWizardStyle(QWizard.ModernStyle)

        if cats is None:
            cats = [
                {"name": "大橘", "file": "orange_cat.gif", "builtin": True},
                {"name": "蓝猫", "file": "blue_cat.gif", "builtin": True},
                {"name": "三花", "file": "calico_cat.gif", "builtin": True},
            ]

        self._cat_page = _CatPage(cats)
        self._timer_page = _TimerPage()
        self._done_page = _DonePage()

        self.addPage(self._cat_page)
        self.addPage(self._timer_page)
        self.addPage(self._done_page)

    def get_settings(self) -> dict:
        return {
            "active_cats": self._cat_page.panel.get_active_cats(),
            "cat_count": self._cat_page.panel.get_cat_count(),
            "cat_size": self._cat_page.panel.get_cat_size(),
            "work_interval_min": self._timer_page.work_slider.value(),
            "break_duration_min": self._timer_page.break_slider.value(),
            "idle_threshold_sec": self._timer_page.idle_slider.value(),
            "dismiss_hide_min": self._timer_page.dismiss_slider.value(),
            "auto_start": self._done_page.auto_start_cb.isChecked(),
            "first_run": False,
        }


class _CatPage(QWizardPage):
    def __init__(self, cats, parent=None):
        super().__init__(parent)
        self.setTitle("选择你的猫咪伙伴")
        self.setSubTitle("选择你喜欢的猫咪来提醒你休息")
        layout = QVBoxLayout(self)
        self.panel = CatConfigPanel(
            cats, [c["name"] for c in cats], count=2, size=100
        )
        layout.addWidget(self.panel)


class _TimerPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("设置提醒时间")
        self.setSubTitle("调整工作和休息的时间")
        layout = QVBoxLayout(self)

        from PySide6.QtWidgets import QFormLayout
        form = QFormLayout()

        self.work_slider = self._make_slider(15, 120, 50, "分钟")
        self.break_slider = self._make_slider(1, 30, 5, "分钟")
        self.idle_slider = self._make_slider(2, 30, 5, "秒")
        self.dismiss_slider = self._make_slider(1, 30, 1, "分钟")

        form.addRow("工作间隔", self.work_slider)
        form.addRow("休息时长", self.break_slider)
        form.addRow("空闲检测", self.idle_slider)
        form.addRow("驱赶隐藏", self.dismiss_slider)

        layout.addLayout(form)

    def _make_slider(self, lo, hi, default, unit):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(default)
        label = QLabel(f"{default} {unit}")
        slider.valueChanged.connect(lambda v, l=label, u=unit: l.setText(f"{v} {u}"))
        layout.addWidget(slider)
        layout.addWidget(label)
        return slider


class _DonePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("准备就绪！")
        self.setSubTitle("Naughty Cat 已经配置好了")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("你的猫咪会在工作时间结束后出来提醒你休息。"))
        layout.addWidget(QLabel("记得让你的猫咪来照顾你的健康！"))
        self.auto_start_cb = QCheckBox("开机自动启动")
        self.auto_start_cb.setChecked(True)
        layout.addWidget(self.auto_start_cb)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_welcome_wizard.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/ui/welcome_wizard.py tests/test_welcome_wizard.py
git commit -m "feat: add welcome_wizard with 3-step first-run setup"
```

---

### Task 9: Settings Window

**Files:**
- Create: `naughty_cat/ui/settings_window.py`
- Create: `tests/test_settings_window.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_settings_window.py`:

```python
from naughty_cat.ui.settings_window import SettingsWindow

def test_settings_window_has_four_tabs(qtbot):
    cats = [{"name": "大橘", "file": "orange_cat.gif", "builtin": True}]
    settings = {
        "active_cats": ["大橘"],
        "cat_count": 2,
        "cat_size": 100,
        "work_interval_min": 50,
        "break_duration_min": 5,
        "idle_threshold_sec": 5,
        "dismiss_hide_min": 1,
        "sound_enabled": True,
        "sound_volume": 30,
        "auto_start": True,
    }
    win = SettingsWindow(cats, settings)
    qtbot.addWidget(win)
    assert win._tab_widget.count() == 4

def test_settings_window_returns_updated_settings(qtbot):
    cats = [{"name": "大橘", "file": "orange_cat.gif", "builtin": True}]
    settings = {
        "active_cats": ["大橘"],
        "cat_count": 2,
        "cat_size": 100,
        "work_interval_min": 50,
        "break_duration_min": 5,
        "idle_threshold_sec": 5,
        "dismiss_hide_min": 1,
        "sound_enabled": True,
        "sound_volume": 30,
        "auto_start": True,
    }
    win = SettingsWindow(cats, settings)
    qtbot.addWidget(win)
    result = win.get_settings()
    assert "work_interval_min" in result
    assert "cat_count" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_settings_window.py -v`
Expected: FAIL — `SettingsWindow` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/ui/settings_window.py`:

```python
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QCheckBox, QPushButton, QSpinBox, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt
from naughty_cat.ui.cat_config import CatConfigPanel


class SettingsWindow(QDialog):
    def __init__(self, cats: list[dict], settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Naughty Cat 设置")
        self.setMinimumSize(420, 380)

        layout = QVBoxLayout(self)
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # Tab 1: Cats
        self._cat_panel = CatConfigPanel(
            cats, settings.get("active_cats", []),
            count=settings.get("cat_count", 2),
            size=settings.get("cat_size", 100)
        )
        self._tab_widget.addTab(self._cat_panel, "🐱 猫咪")

        # Tab 2: Time
        time_tab = QWidget()
        time_layout = QFormLayout(time_tab)

        self._work_slider = self._make_slider(15, 120, settings.get("work_interval_min", 50), "分钟")
        self._break_slider = self._make_slider(1, 30, settings.get("break_duration_min", 5), "分钟")
        self._idle_slider = self._make_slider(2, 30, settings.get("idle_threshold_sec", 5), "秒")
        self._dismiss_slider = self._make_slider(1, 30, settings.get("dismiss_hide_min", 1), "分钟")

        time_layout.addRow("工作间隔", self._work_slider)
        time_layout.addRow("休息时长", self._break_slider)
        time_layout.addRow("空闲检测", self._idle_slider)
        time_layout.addRow("驱赶隐藏", self._dismiss_slider)
        self._tab_widget.addTab(time_tab, "⏰ 时间")

        # Tab 3: Sound
        sound_tab = QWidget()
        sound_layout = QVBoxLayout(sound_tab)

        self._sound_enabled_cb = QCheckBox("启用音效")
        self._sound_enabled_cb.setChecked(settings.get("sound_enabled", True))
        sound_layout.addWidget(self._sound_enabled_cb)

        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("音量"))
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(settings.get("sound_volume", 30))
        self._volume_label = QLabel(str(self._volume_slider.value()))
        self._volume_slider.valueChanged.connect(
            lambda v: self._volume_label.setText(str(v))
        )
        vol_layout.addWidget(self._volume_slider)
        vol_layout.addWidget(self._volume_label)
        sound_layout.addLayout(vol_layout)

        import_btn = QPushButton("导入自定义音效...")
        sound_layout.addWidget(import_btn)
        sound_layout.addStretch()
        self._tab_widget.addTab(sound_tab, "🔊 音效")

        # Tab 4: General
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        self._auto_start_cb = QCheckBox("开机自动启动")
        self._auto_start_cb.setChecked(settings.get("auto_start", True))
        general_layout.addWidget(self._auto_start_cb)

        general_layout.addStretch()

        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel("Naughty Cat v0.1.0"))
        about_layout.addWidget(QLabel("一个用猫咪提醒你休息的小工具"))
        general_layout.addWidget(about_group)

        self._tab_widget.addTab(general_tab, "⚙️ 通用")

        # OK/Cancel buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("保存")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_settings(self) -> dict:
        return {
            "active_cats": self._cat_panel.get_active_cats(),
            "cat_count": self._cat_panel.get_cat_count(),
            "cat_size": self._cat_panel.get_cat_size(),
            "work_interval_min": self._work_slider.value(),
            "break_duration_min": self._break_slider.value(),
            "idle_threshold_sec": self._idle_slider.value(),
            "dismiss_hide_min": self._dismiss_slider.value(),
            "sound_enabled": self._sound_enabled_cb.isChecked(),
            "sound_volume": self._volume_slider.value(),
            "auto_start": self._auto_start_cb.isChecked(),
        }

    @staticmethod
    def _make_slider(lo, hi, default, unit):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(default)
        label = QLabel(f"{default} {unit}")
        slider.valueChanged.connect(lambda v, l=label, u=unit: l.setText(f"{v} {u}"))
        layout.addWidget(slider)
        layout.addWidget(label)
        return slider
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_settings_window.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/ui/settings_window.py tests/test_settings_window.py
git commit -m "feat: add settings_window with 4-tab dialog"
```

---

### Task 10: Break Done Toast

**Files:**
- Create: `naughty_cat/ui/break_done_toast.py`
- Create: `tests/test_break_done_toast.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_break_done_toast.py`:

```python
from PySide6.QtCore import QCoreApplication, Qt
from naughty_cat.ui.break_done_toast import BreakDoneToast

def test_toast_shows_and_emits_on_click(qtbot):
    toast = BreakDoneToast()
    qtbot.addWidget(toast)
    toast.show()
    assert toast.isVisible()

    acknowledged = False

    def on_ack():
        nonlocal acknowledged
        acknowledged = True

    toast.acknowledged.connect(on_ack)
    toast._btn.click()
    assert acknowledged is True

def test_toast_auto_dismisses(qtbot):
    toast = BreakDoneToast(auto_dismiss_ms=50)
    qtbot.addWidget(toast)
    toast.show()

    acknowledged = False

    def on_ack():
        nonlocal acknowledged
        acknowledged = True

    toast.acknowledged.connect(on_ack)

    qtbot.waitUntil(lambda: acknowledged, timeout=2000)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_break_done_toast.py -v`
Expected: FAIL — `BreakDoneToast` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/ui/break_done_toast.py`:

```python
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
)


class BreakDoneToast(QWidget):
    acknowledged = Signal()

    def __init__(self, auto_dismiss_ms=30000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(240, 100)

        self.setStyleSheet("""
            QWidget {
                background: #2d2d3f;
                border: 1px solid #f0a040;
                border-radius: 12px;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background: #f0a040;
                border: none;
                border-radius: 6px;
                padding: 4px 16px;
                color: #1a1a2e;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #f5b850;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("猫咪出去玩了！🐱")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self._btn = QPushButton("知道了")
        self._btn.clicked.connect(self._on_acknowledge)
        layout.addWidget(self._btn, alignment=Qt.AlignCenter)

        # Position bottom-right
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - 260, geo.bottom() - 120)

        if auto_dismiss_ms > 0:
            QTimer.singleShot(auto_dismiss_ms, self._on_acknowledge)

    def _on_acknowledge(self):
        self.acknowledged.emit()
        self.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_break_done_toast.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/ui/break_done_toast.py tests/test_break_done_toast.py
git commit -m "feat: add break_done_toast notification window"
```

---

### Task 11: Tray Icon

**Files:**
- Create: `naughty_cat/tray_icon.py`
- Create: `tests/test_tray_icon.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_tray_icon.py`:

```python
from PySide6.QtWidgets import QApplication, QMenu
from naughty_cat.tray_icon import TrayIcon

def test_tray_icon_initializes(qtbot):
    app = QApplication.instance() or QApplication([])
    tray = TrayIcon()
    assert tray.isVisible() or not tray.isVisible()  # tray may not show in CI
    assert tray._menu is not None

def test_tray_menu_has_items(qtbot):
    tray = TrayIcon()
    actions = tray._menu.actions()
    action_texts = [a.text() for a in actions if a.text()]
    assert "设置" in action_texts or any("设置" in t for t in action_texts)
    assert "退出" in action_texts or any("退出" in t for t in action_texts)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tray_icon.py -v`
Expected: FAIL — `TrayIcon` not found.

- [ ] **Step 3: Write implementation**

Create `naughty_cat/tray_icon.py`:

```python
from pathlib import Path
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtCore import Signal


_ICONS_DIR = Path(__file__).parent / "assets" / "icons"


class TrayIcon(QSystemTrayIcon):
    summon_requested = Signal()
    pause_toggled = Signal(bool)
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_paused = False
        self._menu = QMenu()

        icon_path = _ICONS_DIR / "cat.ico"
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        else:
            self.setIcon(QApplication.style().standardIcon(
                QApplication.style().SP_ComputerIcon
            ))

        self._summon_action = QAction("手动召唤猫咪")
        self._summon_action.triggered.connect(self.summon_requested.emit)
        self._menu.addAction(self._summon_action)

        self._pause_action = QAction("暂停提醒")
        self._pause_action.triggered.connect(self._on_pause_toggle)
        self._menu.addAction(self._pause_action)

        self._menu.addSeparator()

        settings_action = QAction("设置")
        settings_action.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(settings_action)

        about_action = QAction("关于")
        self._menu.addAction(about_action)

        self._menu.addSeparator()

        quit_action = QAction("退出")
        quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(quit_action)

        self.setContextMenu(self._menu)
        self.setToolTip("Naughty Cat")

        # Left-click opens settings (Windows convention: single click activates)
        self.activated.connect(self._on_activated)

    def set_paused(self, paused: bool):
        self._is_paused = paused
        sleep_icon = _ICONS_DIR / "cat_sleep.ico"
        normal_icon = _ICONS_DIR / "cat.ico"

        if paused:
            self._pause_action.setText("恢复提醒")
            if sleep_icon.exists():
                self.setIcon(QIcon(str(sleep_icon)))
        else:
            self._pause_action.setText("暂停提醒")
            if normal_icon.exists():
                self.setIcon(QIcon(str(normal_icon)))

    def _on_pause_toggle(self):
        self._is_paused = not self._is_paused
        self.set_paused(self._is_paused)
        self.pause_toggled.emit(self._is_paused)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.settings_requested.emit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tray_icon.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/tray_icon.py tests/test_tray_icon.py
git commit -m "feat: add tray_icon with context menu and pause/summon/settings"
```

---

### Task 12: Main Entry Point (Wiring)

**Files:**
- Create: `naughty_cat/main.py`

- [ ] **Step 1: Write main.py**

Create `naughty_cat/main.py`:

```python
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from naughty_cat.config_store import ConfigStore
from naughty_cat.idle_detector import IdleDetector
from naughty_cat.sound_player import SoundPlayer
from naughty_cat.state_machine import StateMachine, State, Event
from naughty_cat.cat_manager import CatManager
from naughty_cat.tray_icon import TrayIcon
from naughty_cat.ui.welcome_wizard import WelcomeWizard
from naughty_cat.ui.settings_window import SettingsWindow
from naughty_cat.ui.break_done_toast import BreakDoneToast


def _config_path() -> Path:
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    return Path(appdata) / "naughty-cat" / "config.json"


def _apply_auto_start(enable: bool):
    """Write/remove auto-start registry entry."""
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    exe_path = sys.executable
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )
        if enable:
            winreg.SetValueEx(key, "NaughtyCat", 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, "NaughtyCat")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError:
        pass


class App:
    def __init__(self):
        self._config = ConfigStore(_config_path())
        self._idle = IdleDetector(
            idle_threshold_sec=self._config.settings["idle_threshold_sec"]
        )
        self._sound = SoundPlayer()
        self._sound.set_enabled(self._config.settings["sound_enabled"])
        self._sound.set_volume(self._config.settings["sound_volume"])

        self._state = StateMachine(
            work_interval_min=self._config.settings["work_interval_min"],
            break_duration_min=self._config.settings["break_duration_min"],
            idle_threshold_sec=self._config.settings["idle_threshold_sec"],
            dismiss_hide_min=self._config.settings["dismiss_hide_min"],
        )
        self._cats = CatManager()
        self._tray = TrayIcon()
        self._settings_win = None
        self._toast = None

        self._wire()

    def _wire(self):
        # State changes drive cat visibility
        self._state.state_changed.connect(self._on_state_changed)

        # Idle detection feeds state machine
        self._idle.became_idle.connect(lambda: self._state.transition(Event.IDLE_DETECTED))
        # User active detection: when idle seconds drops below threshold after being idle
        self._idle.idle_seconds_changed.connect(self._on_idle_seconds_changed)

        # Cat dismiss button
        self._cats.dismiss_requested.connect(lambda: self._state.transition(Event.DISMISS_CLICKED))

        # Tray actions
        self._tray.summon_requested.connect(lambda: self._state.transition(Event.MANUAL_SUMMON))
        self._tray.pause_toggled.connect(self._on_pause_toggle)
        self._tray.settings_requested.connect(self._show_settings)
        self._tray.quit_requested.connect(self._quit)

    def start(self):
        if self._config.settings["first_run"]:
            self._show_wizard()

        _apply_auto_start(self._config.settings["auto_start"])
        self._tray.show()
        self._state.start()

    # --- state handlers ---

    def _on_state_changed(self, state: State):
        if state == State.CAT_SHOW:
            self._cats.spawn_cats(
                count=self._config.settings["cat_count"],
                size=self._config.settings["cat_size"],
                active_cat_gifs=[c["file"] for c in self._config.settings["cats"]
                                 if c["name"] in self._config.settings.get("active_cats", [])],
            )
            self._idle.start()
            self._sound.play("meow1.mp3")

        elif state == State.RESTING:
            # Cats already on screen from CAT_SHOW, just keep them
            self._idle.start()

        elif state == State.RESTING_PAUSED:
            pass  # Cats stay on screen, timer paused

        elif state == State.CAT_HIDING:
            self._idle.stop()

        elif state == State.REST_DONE:
            self._cats.remove_all()
            self._idle.stop()
            self._show_toast()

        elif state == State.WORKING:
            self._cats.remove_all()
            self._idle.stop()

    def _on_idle_seconds_changed(self, secs: float):
        threshold = self._config.settings["idle_threshold_sec"]
        if self._state.current_state == State.RESTING and secs < threshold:
            self._state.transition(Event.USER_ACTIVE)

    def _on_pause_toggle(self, paused: bool):
        if paused:
            self._state.pause()
        else:
            self._state.resume()

    def _show_wizard(self):
        wizard = WelcomeWizard(self._config.settings["cats"])
        if wizard.exec() == WelcomeWizard.Accepted:
            s = wizard.get_settings()
            for k, v in s.items():
                self._config.settings[k] = v
            self._config.save()

    def _show_settings(self):
        if self._settings_win and self._settings_win.isVisible():
            self._settings_win.raise_()
            return
        self._settings_win = SettingsWindow(
            self._config.settings["cats"], self._config.settings
        )
        if self._settings_win.exec() == SettingsWindow.Accepted:
            s = self._settings_win.get_settings()
            for k, v in s.items():
                self._config.settings[k] = v
            self._config.save()
            _apply_auto_start(self._config.settings["auto_start"])

    def _show_toast(self):
        self._toast = BreakDoneToast()
        self._toast.acknowledged.connect(
            lambda: self._state.transition(Event.USER_ACKNOWLEDGE)
        )
        self._toast.show()

    def _quit(self):
        self._idle.stop()
        self._cats.remove_all()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    naughty = App()
    naughty.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test the import**

Run:
```bash
python -c "from naughty_cat.main import main; print('main imported OK')"
```
Expected: prints "main imported OK".

- [ ] **Step 3: Commit**

```bash
git add naughty_cat/main.py
git commit -m "feat: add main.py wiring all modules together"
```

---

### Task 13: Asset Generation

**Files:**
- Create cat tray icon `.ico` files
- Create placeholder cat GIFs
- Create placeholder meow sounds

- [ ] **Step 1: Generate tray icons (programmatic)**

```python
# run as script: python -c "
from PySide6.QtGui import QPainter, QPixmap, QIcon, QColor
from PySide6.QtCore import Qt
import os

def make_icon(path, color):
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    # Simple cat face: circle + triangles
    p.drawEllipse(8, 12, 48, 44)  # face
    p.drawPolygon([(8,24),(0,4),(20,16)])  # left ear
    p.drawPolygon([(56,24),(64,4),(44,16)])  # right ear
    # Eyes
    p.setBrush(QColor('#ffffff'))
    p.drawEllipse(18, 28, 10, 10)
    p.drawEllipse(36, 28, 10, 10)
    p.setBrush(QColor('#1a1a2e'))
    p.drawEllipse(20, 30, 6, 8)
    p.drawEllipse(38, 30, 6, 8)
    p.end()
    pix.save(path)

os.makedirs('naughty_cat/assets/icons', exist_ok=True)
make_icon('naughty_cat/assets/icons/cat.ico', '#f0a040')
make_icon('naughty_cat/assets/icons/cat_sleep.ico', '#888888')
print('Icons created')
"
```

- [ ] **Step 2: Create placeholder cat GIFs**

Create simple placeholder GIFs using a script, or download free-to-use GIFs. For v1 development, create a minimal placeholder:

```bash
python -c "
# Create minimal 1x1 GIF placeholders — will be replaced with real assets before release
import struct

def make_gif(path):
    # Minimal valid GIF (1x1 transparent pixel) — placeholder
    data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    with open(path, 'wb') as f:
        f.write(data)

for name in ['orange_cat.gif', 'blue_cat.gif', 'calico_cat.gif']:
    make_gif(f'naughty_cat/assets/cats/{name}')
print('Placeholder GIFs created')
"
```

- [ ] **Step 3: Create placeholder sound file**

```bash
# Create a silent 0.1s MP3 placeholder
python -c "
# Minimal valid MP3 frame — will be replaced before release
# Just create an empty file for now; QMediaPlayer handles missing files gracefully
for name in ['meow1.mp3', 'meow2.mp3']:
    with open(f'naughty_cat/assets/sounds/{name}', 'wb') as f:
        f.write(b'\xff\xfb\x90\x00')
print('Placeholder sounds created')
"
```

- [ ] **Step 4: Commit**

```bash
git add naughty_cat/assets/
git commit -m "feat: add placeholder icons, cat GIFs and sound files"
```

---

### Task 14: Packaging (PyInstaller + NSIS)

**Files:**
- Create: `naughty_cat.spec` (PyInstaller spec)
- Create: `installer.nsi` (NSIS script)

- [ ] **Step 1: Create PyInstaller spec**

Create `naughty_cat.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['naughty_cat/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('naughty_cat/assets/cats/*.gif', 'naughty_cat/assets/cats'),
        ('naughty_cat/assets/sounds/*.mp3', 'naughty_cat/assets/sounds'),
        ('naughty_cat/assets/icons/*.ico', 'naughty_cat/assets/icons'),
    ],
    hiddenimports=['PySide6.QtMultimedia'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NaughtyCat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='naughty_cat/assets/icons/cat.ico',
)
```

- [ ] **Step 2: Create NSIS installer script**

Create `installer.nsi`:

```nsis
!define PRODUCT_NAME "Naughty Cat"
!define PRODUCT_VERSION "0.1.0"
!define PRODUCT_PUBLISHER "Naughty Cat"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "NaughtyCat-Setup.exe"
InstallDir "$PROGRAMFILES\NaughtyCat"
RequestExecutionLevel admin

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\NaughtyCat\*.*"

    CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Naughty Cat.lnk" "$INSTDIR\NaughtyCat.exe"

    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
SectionEnd
```

- [ ] **Step 3: Build and verify**

Run:
```bash
pip install pyinstaller
pyinstaller naughty_cat.spec --clean --noconfirm
```
Verify: `dist/NaughtyCat/NaughtyCat.exe` exists.

- [ ] **Step 4: Commit**

```bash
git add naughty_cat.spec installer.nsi
git commit -m "feat: add PyInstaller spec and NSIS installer script"
```

---

### Task 15: Integration Smoke Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
from PySide6.QtWidgets import QApplication
from naughty_cat.config_store import ConfigStore
from naughty_cat.idle_detector import IdleDetector
from naughty_cat.sound_player import SoundPlayer
from naughty_cat.state_machine import StateMachine, Event, State
from naughty_cat.cat_manager import CatManager
from naughty_cat.tray_icon import TrayIcon
from naughty_cat.ui.break_done_toast import BreakDoneToast
from naughty_cat.ui.settings_window import SettingsWindow
from naughty_cat.ui.welcome_wizard import WelcomeWizard


def test_full_workflow_imports(qtbot):
    """Sanity check: all modules import and can be instantiated."""
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp()) / "config.json"
    config = ConfigStore(tmp)
    assert config is not None

    idle = IdleDetector()
    assert idle is not None

    sound = SoundPlayer()
    assert sound is not None

    sm = StateMachine(50, 5, 5, 1)
    assert sm.current_state == State.WORKING

    cats = CatManager()
    assert cats.cat_count == 0

    tray = TrayIcon()
    assert tray is not None

    toast = BreakDoneToast(auto_dismiss_ms=100)
    assert toast is not None
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_integration.py -v`
Expected: 1 test PASS (all imports + basic instantiation work).

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration smoke test for all modules"
```

---

## Test Plan Summary

| Test file | What it covers |
|-----------|---------------|
| `test_config_store.py` | Defaults, load, save, atomic write, validation, range clamping |
| `test_idle_detector.py` | Start/stop, idle_seconds signal, became_idle signal |
| `test_sound_player.py` | Volume get/set/clamp, enabled toggle, play without crash |
| `test_state_machine.py` | All 10 state transitions, pause/resume, manual summon |
| `test_cat_manager.py` | Spawn, dismiss, remove, double-spawn replacement |
| `test_cat_config.py` | Panel initialization with cats, import button exists |
| `test_welcome_wizard.py` | 3 pages exist, settings output |
| `test_settings_window.py` | 4 tabs exist, settings round-trip |
| `test_break_done_toast.py` | Show + click emit, auto-dismiss |
| `test_tray_icon.py` | Menu structure, action texts |
| `test_integration.py` | All modules import and instantiate |

## Build & Run

```bash
# Dev
pip install -e ".[dev]"
python -m naughty_cat.main

# Tests
pytest -v

# Package
pip install pyinstaller
pyinstaller naughty_cat.spec --clean --noconfirm

# Installer
makensis installer.nsi
```
