# Immediate Settings Application & Timer Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make settings changes apply immediately without restart, and show a real-time timer countdown in the settings window.

**Architecture:** Four files modified in dependency order: `idle_detector.py` (add `update_threshold()`), `state_machine.py` (add `update_intervals()` + `timer_info()`), `settings_window.py` (add timer status card with polling), `main.py` (wire calls after settings save). Each change is independently testable.

**Tech Stack:** Python 3.12, PySide6, pytest-qt

---

## File Structure

| File | Role |
|------|------|
| `naughty_cat/idle_detector.py` | Add `update_threshold(secs)` — one-line setter |
| `naughty_cat/state_machine.py` | Add `update_intervals()` — runtime interval changes with elapsed preservation; `timer_info()` — read-only state snapshot |
| `naughty_cat/ui/settings_window.py` | Accept `timer_info_cb`, add status card frame in time tab, 1s poll timer |
| `naughty_cat/main.py` | Call `update_intervals()` + `update_threshold()` after settings save; pass `timer_info_cb` to SettingsWindow |

---

### Task 1: IdleDetector.update_threshold()

**Files:**
- Modify: `naughty_cat/idle_detector.py`
- Modify: `tests/test_idle_detector.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_idle_detector.py`:

```python
def test_update_threshold():
    detector = IdleDetector(idle_threshold_sec=5)
    assert detector._idle_threshold == 5
    detector.update_threshold(10)
    assert detector._idle_threshold == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_idle_detector.py::test_update_threshold -v`
Expected: FAIL — `IdleDetector` has no attribute `update_threshold`

- [ ] **Step 3: Write implementation**

In `naughty_cat/idle_detector.py`, add after `stop()`:

```python
    def update_threshold(self, idle_threshold_sec: float):
        self._idle_threshold = idle_threshold_sec
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_idle_detector.py::test_update_threshold -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/idle_detector.py tests/test_idle_detector.py
git commit -m "feat: add IdleDetector.update_threshold() for runtime threshold changes"
```

---

### Task 2: StateMachine.update_intervals()

**Files:**
- Modify: `naughty_cat/state_machine.py`
- Modify: `tests/test_state_machine.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_state_machine.py`:

```python
def test_update_intervals_updates_stored_values():
    app = QCoreApplication.instance() or QCoreApplication([])
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm.update_intervals(work_interval_min=30, break_duration_min=10,
                        dismiss_hide_min=3)
    assert sm._work_interval_ms == 30 * 60 * 1000
    assert sm._break_duration_ms == 10 * 60 * 1000
    assert sm._dismiss_hide_ms == 3 * 60 * 1000


def test_update_intervals_while_working_preserves_elapsed(qtbot):
    sm = StateMachine(work_interval_min=0.001, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm._start_work_timer()
    assert sm._work_timer.isActive()
    remaining_before = sm._work_timer.remainingTime()
    # Change to 60 min — remaining should jump way up (most of 60 min left)
    sm.update_intervals(work_interval_min=60, break_duration_min=5,
                        dismiss_hide_min=1)
    remaining_after = sm._work_timer.remainingTime()
    assert remaining_after > remaining_before
    # Should be close to 60 min (minus the few ms elapsed)
    assert remaining_after > 50 * 60 * 1000


def test_update_intervals_during_resting_does_not_interrupt(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=0.001,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING)
    sm._start_break_timer()
    remaining_before = sm._break_timer.remainingTime()
    sm.update_intervals(work_interval_min=30, break_duration_min=60,
                        dismiss_hide_min=3)
    # Break timer is NOT interrupted, still running with old short value
    assert sm._break_timer.isActive()
    assert sm._break_timer.remainingTime() < 2000


def test_update_intervals_when_idle_does_not_restart_timer(qtbot):
    """When no timer is active (e.g. CAT_SHOW), update_intervals just stores values."""
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.CAT_SHOW)
    sm.update_intervals(work_interval_min=30, break_duration_min=10,
                        dismiss_hide_min=3)
    assert sm._work_interval_ms == 30 * 60 * 1000
    assert sm._break_duration_ms == 10 * 60 * 1000
    assert sm._dismiss_hide_ms == 3 * 60 * 1000
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state_machine.py::test_update_intervals_updates_stored_values tests/test_state_machine.py::test_update_intervals_while_working_preserves_elapsed tests/test_state_machine.py::test_update_intervals_during_resting_does_not_interrupt tests/test_state_machine.py::test_update_intervals_when_idle_does_not_restart_timer -v`
Expected: 4 FAIL — `StateMachine` has no attribute `update_intervals`

- [ ] **Step 3: Write implementation**

In `naughty_cat/state_machine.py`, add after `resume()`:

```python
    def update_intervals(self, work_interval_min, break_duration_min,
                         dismiss_hide_min):
        old_work_ms = self._work_interval_ms
        self._work_interval_ms = int(work_interval_min * 60 * 1000)
        self._break_duration_ms = int(break_duration_min * 60 * 1000)
        self._dismiss_hide_ms = int(dismiss_hide_min * 60 * 1000)

        if self._current_state == State.WORKING and self._work_timer.isActive():
            remaining = self._work_timer.remainingTime()
            elapsed = old_work_ms - remaining
            new_remaining = max(0, self._work_interval_ms - elapsed)
            self._work_timer.start(new_remaining)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_state_machine.py::test_update_intervals_updates_stored_values tests/test_state_machine.py::test_update_intervals_while_working_preserves_elapsed tests/test_state_machine.py::test_update_intervals_during_resting_does_not_interrupt tests/test_state_machine.py::test_update_intervals_when_idle_does_not_restart_timer -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/state_machine.py tests/test_state_machine.py
git commit -m "feat: add StateMachine.update_intervals() for runtime interval changes"
```

---

### Task 3: StateMachine.timer_info()

**Files:**
- Modify: `naughty_cat/state_machine.py`
- Modify: `tests/test_state_machine.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_state_machine.py`:

```python
def test_timer_info_while_working(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm._start_work_timer()
    info = sm.timer_info()
    assert info["state"] == State.WORKING
    assert info["remaining_ms"] is not None
    assert info["total_ms"] == 50 * 60 * 1000


def test_timer_info_while_resting(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING)
    sm._start_break_timer()
    info = sm.timer_info()
    assert info["state"] == State.RESTING
    assert info["remaining_ms"] is not None
    assert info["total_ms"] == 5 * 60 * 1000


def test_timer_info_while_hiding(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.CAT_HIDING)
    sm._start_hide_timer()
    info = sm.timer_info()
    assert info["state"] == State.CAT_HIDING
    assert info["remaining_ms"] is not None
    assert info["total_ms"] == 1 * 60 * 1000


def test_timer_info_resting_paused(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING_PAUSED)
    info = sm.timer_info()
    assert info["state"] == State.RESTING_PAUSED
    assert info["remaining_ms"] is not None
    assert info["total_ms"] == 5 * 60 * 1000


def test_timer_info_no_timer_states(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    for state in [State.CAT_SHOW, State.REST_DONE]:
        sm._force_state(state)
        info = sm.timer_info()
        assert info["state"] == state
        assert info["remaining_ms"] is None
        assert info["total_ms"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_state_machine.py::test_timer_info_while_working tests/test_state_machine.py::test_timer_info_while_resting tests/test_state_machine.py::test_timer_info_while_hiding tests/test_state_machine.py::test_timer_info_resting_paused tests/test_state_machine.py::test_timer_info_no_timer_states -v`
Expected: 5 FAIL — `StateMachine` has no attribute `timer_info`

- [ ] **Step 3: Write implementation**

In `naughty_cat/state_machine.py`, add after `update_intervals()`:

```python
    def timer_info(self) -> dict:
        info = {
            "state": self._current_state,
            "remaining_ms": None,
            "total_ms": None,
        }
        if self._current_state == State.WORKING and self._work_timer.isActive():
            info["remaining_ms"] = self._work_timer.remainingTime()
            info["total_ms"] = self._work_interval_ms
        elif self._current_state == State.RESTING and self._break_timer.isActive():
            info["remaining_ms"] = self._break_timer.remainingTime()
            info["total_ms"] = self._break_duration_ms
        elif self._current_state == State.RESTING_PAUSED:
            info["remaining_ms"] = self._break_remaining_ms or self._break_duration_ms
            info["total_ms"] = self._break_duration_ms
        elif self._current_state == State.CAT_HIDING and self._hide_timer.isActive():
            info["remaining_ms"] = self._hide_timer.remainingTime()
            info["total_ms"] = self._dismiss_hide_ms
        return info
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_state_machine.py::test_timer_info_while_working tests/test_state_machine.py::test_timer_info_while_resting tests/test_state_machine.py::test_timer_info_while_hiding tests/test_state_machine.py::test_timer_info_resting_paused tests/test_state_machine.py::test_timer_info_no_timer_states -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/state_machine.py tests/test_state_machine.py
git commit -m "feat: add StateMachine.timer_info() for real-time timer status"
```

---

### Task 4: SettingsWindow Timer Status Card

**Files:**
- Modify: `naughty_cat/ui/settings_window.py`
- Modify: `tests/test_settings_window.py`

- [ ] **Step 1: Write failing tests**

Replace `tests/test_settings_window.py`:

```python
from naughty_cat.ui.settings_window import SettingsWindow
from naughty_cat.state_machine import State, StateMachine


def test_settings_window_has_four_tabs(qtbot):
    cats = [{"name": "波仔", "file": "orange_cat.gif", "builtin": True}]
    settings = {
        "active_cats": ["波仔"],
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
    cats = [{"name": "波仔", "file": "orange_cat.gif", "builtin": True}]
    settings = {
        "active_cats": ["波仔"],
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


def test_timer_status_card_created_when_callback_provided(qtbot):
    cats = [{"name": "波仔", "file": "orange_cat.gif", "builtin": True}]
    settings = {
        "active_cats": ["波仔"],
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
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm._start_work_timer()
    win = SettingsWindow(cats, settings, timer_info_cb=sm.timer_info)
    qtbot.addWidget(win)
    # Status card should exist and be visible
    assert win._timer_status_card is not None
    assert not win._timer_status_card.isHidden()


def test_timer_status_card_hidden_without_callback(qtbot):
    cats = [{"name": "波仔", "file": "orange_cat.gif", "builtin": True}]
    settings = {
        "active_cats": ["波仔"],
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
    win = SettingsWindow(cats, settings)  # no callback
    qtbot.addWidget(win)
    assert win._timer_status_card.isHidden()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_settings_window.py::test_timer_status_card_created_when_callback_provided tests/test_settings_window.py::test_timer_status_card_hidden_without_callback -v`
Expected: 2 FAIL — `SettingsWindow` has no attribute `_timer_status_card`

- [ ] **Step 3: Write implementation**

Modify `naughty_cat/ui/settings_window.py` — the full file:

```python
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QCheckBox, QPushButton, QSpinBox, QFormLayout, QGroupBox, QWidget,
    QFileDialog, QFrame, QSizePolicy
)
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from naughty_cat.ui.cat_config import CatConfigPanel
from naughty_cat.ui.style import make_slider_row
from naughty_cat.state_machine import State


class SettingsWindow(QDialog):
    def __init__(self, cats: list[dict], settings: dict, timer_info_cb=None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Naughty Cat 设置")
        self.setMinimumSize(480, 460)

        self._timer_info_cb = timer_info_cb

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
        time_layout = QVBoxLayout(time_tab)

        # Timer status card
        self._timer_status_card = self._build_timer_status_card()
        time_layout.addWidget(self._timer_status_card)

        form_layout = QFormLayout()
        self._work_slider, work_row = make_slider_row(
            3, 120, settings.get("work_interval_min", 50), "分钟")
        self._break_slider, break_row = make_slider_row(
            1, 30, settings.get("break_duration_min", 5), "分钟")
        self._idle_slider, idle_row = make_slider_row(
            2, 30, settings.get("idle_threshold_sec", 5), "秒")
        self._dismiss_slider, dismiss_row = make_slider_row(
            1, 30, settings.get("dismiss_hide_min", 1), "分钟")

        form_layout.addRow("工作间隔", work_row)
        form_layout.addRow("休息时长", break_row)
        form_layout.addRow("空闲检测", idle_row)
        form_layout.addRow("驱赶隐藏", dismiss_row)
        time_layout.addLayout(form_layout)
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

        self._imported_sounds = list(settings.get("custom_sounds", []))
        self._sound_list_label = QLabel()
        self._update_sound_list_label()
        sound_layout.addWidget(self._sound_list_label)

        self._sound_import_btn = QPushButton("导入自定义音效...")
        self._sound_import_btn.clicked.connect(self._import_sound)
        sound_layout.addWidget(self._sound_import_btn)
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

        # Start poll timer if callback provided
        self._poll_timer = None
        if self._timer_info_cb:
            self._refresh_timer_display()
            self._poll_timer = QTimer(self)
            self._poll_timer.setInterval(1000)
            self._poll_timer.timeout.connect(self._refresh_timer_display)
            self._poll_timer.start()

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
            "custom_sounds": self._imported_sounds,
            "auto_start": self._auto_start_cb.isChecked(),
        }

    def _build_timer_status_card(self):
        card = QFrame()
        card.setObjectName("timerStatusCard")
        card.setStyleSheet("""
            QFrame#timerStatusCard {
                background: #3d3d5c;
                border-radius: 10px;
                padding: 12px 16px;
            }
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)

        self._timer_emoji = QLabel()
        self._timer_emoji.setStyleSheet("font-size: 28px;")
        card_layout.addWidget(self._timer_emoji)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self._timer_state_label = QLabel()
        self._timer_state_label.setStyleSheet("color: #888; font-size: 11px;")
        info_layout.addWidget(self._timer_state_label)

        self._timer_countdown = QLabel()
        self._timer_countdown.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self._timer_countdown)

        # Progress bar
        self._timer_progress_bg = QWidget()
        self._timer_progress_bg.setFixedHeight(6)
        self._timer_progress_bg.setStyleSheet(
            "background: #2a2a3f; border-radius: 3px;")
        self._timer_progress_fill = QWidget(self._timer_progress_bg)
        self._timer_progress_fill.setFixedHeight(6)
        self._timer_progress_fill.setStyleSheet(
            "background: #f0a040; border-radius: 3px;")

        info_layout.addWidget(self._timer_progress_bg)

        info_layout.addStretch()
        card_layout.addLayout(info_layout, 1)
        card.setVisible(False)
        return card

    def _refresh_timer_display(self):
        if not self._timer_info_cb:
            return
        info = self._timer_info_cb()
        if info["remaining_ms"] is None:
            self._timer_status_card.setVisible(False)
            return

        self._timer_status_card.setVisible(True)
        state = info["state"]
        remaining_ms = info["remaining_ms"]
        total_ms = info["total_ms"]
        progress = max(0.0, min(1.0, 1.0 - remaining_ms / total_ms)) if total_ms else 0.0

        if state == State.WORKING:
            remaining_min = remaining_ms / 60000
            self._timer_emoji.setText("🐱")
            self._timer_state_label.setText("当前状态 · 工作中")
            self._timer_countdown.setText(
                f"猫咪还有 {remaining_min:.0f} 分钟过来玩")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #f0a040;")
            self._timer_progress_fill.setStyleSheet(
                "background: #f0a040; border-radius: 3px;")
        elif state == State.CAT_SHOW:
            self._timer_emoji.setText("😺")
            self._timer_state_label.setText("当前状态 · 猫咪出现了！")
            self._timer_countdown.setText("正在等待你休息...")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #f5b860;")
            progress = 0.0
        elif state == State.RESTING:
            remaining_min = remaining_ms / 60000
            self._timer_emoji.setText("😴")
            self._timer_state_label.setText("当前状态 · 休息中")
            self._timer_countdown.setText(
                f"还剩 {remaining_min:.0f} 分钟")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #5cba80;")
            self._timer_progress_fill.setStyleSheet(
                "background: #5cba80; border-radius: 3px;")
        elif state == State.RESTING_PAUSED:
            self._timer_emoji.setText("🙀")
            self._timer_state_label.setText("当前状态 · 休息暂停")
            self._timer_countdown.setText("检测到活动，休息计时暂停中...")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #d0a050;")
            self._timer_progress_fill.setStyleSheet(
                "background: #d0a050; border-radius: 3px;")
        elif state == State.CAT_HIDING:
            remaining_sec = remaining_ms / 1000
            self._timer_emoji.setText("🙈")
            self._timer_state_label.setText("当前状态 · 猫藏起来了")
            self._timer_countdown.setText(
                f"猫咪 {remaining_sec:.0f} 秒后再次出现")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #d08060;")
            self._timer_progress_fill.setStyleSheet(
                "background: #d08060; border-radius: 3px;")
        elif state == State.REST_DONE:
            self._timer_emoji.setText("✅")
            self._timer_state_label.setText("当前状态 · 休息完成！")
            self._timer_countdown.setText("点击「知道了」继续工作")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #5cb85c;")
            progress = 0.0
        else:
            self._timer_status_card.setVisible(False)
            return

        # Update progress bar width
        bg_width = self._timer_progress_bg.width()
        if bg_width > 0:
            self._timer_progress_fill.setFixedWidth(int(bg_width * progress))

    def _import_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入音效", "",
            "Audio (*.mp3 *.wav *.ogg *.m4a);;All Files (*)"
        )
        if not path:
            return
        if path not in self._imported_sounds:
            self._imported_sounds.append(path)
        self._update_sound_list_label()

    def _update_sound_list_label(self):
        if self._imported_sounds:
            names = [Path(p).name for p in self._imported_sounds]
            self._sound_list_label.setText("已导入: " + ", ".join(names))
        else:
            self._sound_list_label.setText("已导入: 无")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_settings_window.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/ui/settings_window.py tests/test_settings_window.py
git commit -m "feat: add timer status card to settings window time tab"
```

---

### Task 5: Wire Everything in App

**Files:**
- Modify: `naughty_cat/main.py`

- [ ] **Step 1: Update _show_settings() to apply settings immediately**

Modify `naughty_cat/main.py` `_show_settings()` method (lines 149-166). Replace the existing method body:

```python
    def _show_settings(self):
        if self._settings_win and self._settings_win.isVisible():
            self._settings_win.raise_()
            return
        self._settings_win = SettingsWindow(
            self._config.settings["cats"],
            self._config.settings,
            timer_info_cb=self._state.timer_info,
        )
        if self._settings_win.exec() == SettingsWindow.Accepted:
            s = self._settings_win.get_settings()
            for k, v in s.items():
                self._config.settings[k] = v
            self._config.save()
            self._sound.set_enabled(self._config.settings["sound_enabled"])
            self._sound.set_volume(self._config.settings["sound_volume"])
            self._sound.set_custom_sounds(
                self._config.settings.get("custom_sounds", [])
            )
            self._state.update_intervals(
                work_interval_min=self._config.settings["work_interval_min"],
                break_duration_min=self._config.settings["break_duration_min"],
                dismiss_hide_min=self._config.settings["dismiss_hide_min"],
            )
            self._idle.update_threshold(
                self._config.settings["idle_threshold_sec"]
            )
            _apply_auto_start(self._config.settings["auto_start"])
```

- [ ] **Step 2: Update _show_wizard() to also apply settings (same pattern)**

Replace `_show_wizard()` method (lines 139-147):

```python
    def _show_wizard(self):
        wizard = WelcomeWizard(self._config.settings["cats"])
        if wizard.exec() == WelcomeWizard.Accepted:
            s = wizard.get_settings()
            for k, v in s.items():
                self._config.settings[k] = v
            self._config.save()
            self._sound.set_enabled(self._config.settings["sound_enabled"])
            self._sound.set_volume(self._config.settings["sound_volume"])
            self._state.update_intervals(
                work_interval_min=self._config.settings["work_interval_min"],
                break_duration_min=self._config.settings["break_duration_min"],
                dismiss_hide_min=self._config.settings["dismiss_hide_min"],
            )
            self._idle.update_threshold(
                self._config.settings["idle_threshold_sec"]
            )
```

- [ ] **Step 3: Verify imports**

Run: `python -c "from naughty_cat.main import main; print('OK')"`
Expected: "OK"

- [ ] **Step 4: Run all tests to verify nothing is broken**

Run: `pytest tests/ -v`
Expected: All existing tests still PASS, plus new tests from Tasks 1-4

- [ ] **Step 5: Commit**

```bash
git add naughty_cat/main.py
git commit -m "feat: apply settings immediately on save and wire timer display"
```

---

## Test Plan Summary

| Test | What it covers |
|------|---------------|
| `test_update_threshold` | IdleDetector threshold updates at runtime |
| `test_update_intervals_updates_stored_values` | Stored ms values change |
| `test_update_intervals_while_working_preserves_elapsed` | Work timer restarts with preserved elapsed |
| `test_update_intervals_during_resting_does_not_interrupt` | Break timer not touched during RESTING |
| `test_update_intervals_when_idle_does_not_restart_timer` | No-op when no active timer |
| `test_timer_info_while_working` | timer_info() returns work timer data |
| `test_timer_info_while_resting` | timer_info() returns break timer data |
| `test_timer_info_while_hiding` | timer_info() returns hide timer data |
| `test_timer_info_resting_paused` | timer_info() returns saved break remaining |
| `test_timer_info_no_timer_states` | timer_info() returns None for CAT_SHOW/REST_DONE |
| `test_timer_status_card_created_when_callback_provided` | Status card visible with callback |
| `test_timer_status_card_hidden_without_callback` | Status card hidden without callback |
