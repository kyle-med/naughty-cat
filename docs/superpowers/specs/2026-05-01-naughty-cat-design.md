# Naughty Cat - Break Reminder App Design Spec

**Date:** 2026-05-01
**Status:** Draft

## Overview

A Windows desktop app that uses animated cat characters to remind the user to take breaks. Cats appear on screen at configurable intervals and playfully occupy the display until the user takes a proper break. Built with Python + PySide6 for fast development and easy maintenance.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Platform | Windows only (cross-platform arch) | Start focused, leave migration path |
| Distribution | MSI installer | Familiar install UX, supports autostart registry |
| Tech stack | Python 3.12 + PySide6 | Fast dev, low memory (~35MB idle), easy to maintain |
| Cat animation | GIF/APNG via QMovie | Simple, abundant assets, swappable files |
| Architecture | Modular components | 6 modules, each single-responsibility, testable independently |

## Architecture

```
naughty_cat/
├── main.py                # Entry point, assembly, startup
├── state_machine.py       # Core state machine
├── cat_manager.py         # Cat window lifecycle & movement
├── idle_detector.py       # Keyboard/mouse idle detection
├── config_store.py        # JSON config read/write
├── sound_player.py        # Audio playback
├── tray_icon.py           # System tray icon & menu
├── ui/
│   ├── welcome_wizard.py  # First-run setup wizard
│   ├── settings_window.py # Settings dialog
│   ├── cat_config.py      # Cat selection/import panel
│   └── break_done_toast.py # "猫咪出去玩了" toast notification
└── assets/
    ├── cats/              # Built-in cat GIFs
    └── sounds/            # Built-in sound effects
```

Each module exposes 2-3 public methods. Internal implementation can change freely without affecting consumers.

## State Machine

```
WORKING ────── work timer fires ──▶ CAT_SHOW
  ▲                                  ├── idle X seconds ──▶ RESTING
  │                                  │                        ├── user active ──▶ RESTING_PAUSED
  │                                  │                        │                    └── idle X sec ──▶ RESTING
  │                                  │                        └── countdown done ──▶ REST_DONE
  │                                  │
  │                                  └── user clicks dismiss ──▶ CAT_HIDING (Y min)
  │                                                                └── timer done ──▶ CAT_SHOW
  │
  └── user clicks "知道了" ── REST_DONE
```

### State Behaviors

| State | Cat on screen? | Timer running? | Idle detection? | Dismiss available? |
|-------|:---:|:---:|:---:|:---:|
| WORKING | No | Work timer | No | N/A |
| CAT_SHOW | Yes | No | Yes | Yes |
| RESTING | Yes | Break countdown | Yes | Yes |
| RESTING_PAUSED | Yes | Break countdown (paused) | Yes | Yes |
| CAT_HIDING | No | Hide timer (Y min) | No | No |
| REST_DONE | No | No | No | Toast notification shown |

## Modules

### idle_detector.py

Polls `GetLastInputInfo()` Win32 API every 500ms via a QTimer. Emits Qt signals: `idle_seconds_changed(n)` and `became_idle`. Pure polling, no hooks needed.

### cat_manager.py

Manages N independent cat windows. Each cat window is:
- A frameless, transparent-background QWidget
- `Qt.WindowStaysOnTopHint` for always-on-top
- `Qt.Tool` flag to avoid appearing in taskbar
- Contains a QLabel with QMovie playing a GIF
- Repositioned every 100ms by a shared QTimer with random walk logic:
  - Pick a random direction (angle)
  - Move at 80-200 px/sec (randomized per cat)
  - Bounce off screen edges
  - On collision with another cat, both change direction
  - Every 3-8 seconds (random), pick new direction even without collision

Each cat has a "dismiss" button. Clicking any cat's dismiss button dimisses ALL cats simultaneously.

`CatManager` public API:
- `spawn_cats(count, size, active_cat_gifs)` — create and show cat windows
- `dismiss_all()` — hide all cats, start hide timer
- `remove_all()` — destroy all cat windows (when break completes)
- Signal: `dismiss_requested`

### state_machine.py

Drives the state transitions. Receives signals from idle_detector and cat_manager. Owns the work timer (QTimer). Exposes `current_state` property and `transition(event)` method.

Events: `WORK_TIMER_FIRE`, `IDLE_DETECTED`, `USER_ACTIVE`, `BREAK_COMPLETE`, `DISMISS_CLICKED`, `HIDE_TIMER_FIRE`, `USER_ACKNOWLEDGE`

### config_store.py

Reads/writes JSON to `%APPDATA%/naughty-cat/config.json`. Atomic writes (write to temp, rename). Validates ranges on load, falls back to defaults for invalid values. Exposes `settings` dict and `save()` method.

Default settings:
```json
{
  "cats": [
    {"name": "大橘", "file": "orange_cat.gif", "builtin": true},
    {"name": "蓝猫", "file": "blue_cat.gif", "builtin": true},
    {"name": "三花", "file": "calico_cat.gif", "builtin": true}
  ],
  "active_cats": ["大橘", "蓝猫", "三花"],
  "cat_count": 2,
  "cat_size": 100,
  "work_interval_min": 50,
  "break_duration_min": 5,
  "idle_threshold_sec": 5,
  "dismiss_hide_min": 1,
  "sound_enabled": true,
  "sound_volume": 30,
  "custom_sounds": [],
  "auto_start": true,
  "first_run": true
}
```

### sound_player.py

Uses QMediaPlayer to play audio files. Supports importing custom sounds. Public API: `play(sound_name)`, `set_volume(int)`, `set_enabled(bool)`.

### tray_icon.py

System tray icon with right-click menu:
- "手动召唤猫咪" — trigger cat appearance immediately
- "暂停提醒" / "恢复提醒" — toggle pause (shows different icon when paused)
- Separator
- "设置" — open settings window
- "关于"
- Separator
- "退出"

Left-click opens settings window. Paused state changes icon to a gray/sleeping variant.

### ui/welcome_wizard.py

Three-step wizard shown on first run:
1. **Pick cats** — grid of built-in cats, toggle selection, option to import custom GIF
2. **Set timers** — sliders for work interval, break duration, idle threshold, dismiss hide time
3. **Done** — summary, toggle auto-start, "开始使用" button

### ui/settings_window.py

Four-tab dialog (shared widgets with wizard for timer/cat settings):
1. **猫咪** — enable/disable cats, import new GIF, adjust cat count & size
2. **时间** — four sliders (work interval, break duration, idle threshold, dismiss hide)
3. **音效** — enable/disable sound, volume slider, preview built-in sounds, import custom
4. **通用** — auto-start toggle, reset settings, about info

### ui/break_done_toast.py

When the break countdown completes (REST_DONE state), a small frameless toast window appears in the bottom-right corner of the screen (above taskbar). Displays "猫咪出去玩了！" with a "知道了" button. Clicking the button or closing the window emits `acknowledged` signal, transitioning to WORKING state. The toast auto-dismisses after 30 seconds if not clicked (treats as acknowledged).

### Tray "暂停提醒" behavior

When "暂停提醒" is clicked, the app enters a paused mode: the work timer stops and no cats will appear. The tray icon changes to a gray/sleeping variant. Right-click menu item changes to "恢复提醒". When resumed, the work timer resets.

### Tray "手动召唤猫咪" behavior

Triggers immediate transition to CAT_SHOW state regardless of current state (unless already in CAT_SHOW, RESTING, RESTING_PAUSED, or CAT_HIDING). Does not affect the work timer — when the break/dismiss cycle completes, the work timer restarts normally.

## Distribution

- PyInstaller to bundle into a single folder
- NSIS or WiX to create MSI installer
- Installer registers auto-start via `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- Installer creates Start Menu shortcut
- Config stored in `%APPDATA%/naughty-cat/`

## Asset Plan

### Built-in Cats
- 3 default cat GIFs (orange tabby, blue/ Russian Blue, calico)
- Source: free-to-use GIF assets or simple stylized drawings
- Format: APNG preferred (better quality/size ratio than GIF), GIF fallback

### Built-in Sounds
- 2-3 short meow/chirp sounds
- Source: royalty-free sound libraries
- Format: MP3

## Scope Boundaries

### In scope
- Core timer/state machine
- Cat overlay windows with random walk
- Idle detection
- Dismiss + hide mechanism
- Break-done toast notification
- System tray with menu
- Welcome wizard + settings window
- Sound effects
- Auto-start management
- Pause/resume reminders
- Manual summon cats
- MSI packaging

### Out of scope (v1)
- Cross-platform support (architecture allows later)
- Break activity suggestions
- Usage statistics
- Pomodoro-style focus sessions
- Cat behavior customization beyond count/size
- Multi-monitor-aware cat positioning (cats may spawn on any monitor randomly)
