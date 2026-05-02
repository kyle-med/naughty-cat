# Immediate Settings Application & Timer Display Design

**Date:** 2026-05-02
**Status:** Draft

## Overview

Two related improvements:
1. Settings changes (work interval, break duration, etc.) apply immediately without restarting the app
2. The settings window's time tab shows a real-time timer status card so the user knows "how long until the cat comes"

## Problem

Currently, `main.py` `_show_settings()` saves config to disk but never updates the running `StateMachine` or `IdleDetector` instances. The new values only take effect on next app launch.

## Design

### 1. StateMachine: `update_intervals()`

Add a method to update timer intervals at runtime:

```
update_intervals(work_interval_min, break_duration_min, dismiss_hide_min)
```

- Store new values in `_work_interval_ms`, `_break_duration_ms`, `_dismiss_hide_ms`
- **If WORKING state and work timer is active:** compute elapsed = old_total - remaining, then new_remaining = max(0, new_total - elapsed), restart work timer with new_remaining. This preserves user's already-worked time.
- **If RESTING / RESTING_PAUSED / CAT_HIDING:** do NOT touch active break/hide timers. They finish with old values. New values are used the next time those timers start.

### 2. StateMachine: `timer_info()`

Add a read-only method returning current timer status for UI display:

```
timer_info() -> dict
```

Returns `{"state": State, "remaining_ms": int | None, "total_ms": int | None}`.

Only includes timing data when a timer is active:
- WORKING with active work timer → remaining/total from work timer
- RESTING with active break timer → remaining/total from break timer
- CAT_HIDING with active hide timer → remaining/total from hide timer
- Other states → remaining_ms and total_ms are None

### 3. IdleDetector: `update_threshold(secs)`

Add a one-line method to update the idle threshold at runtime:

```
update_threshold(secs: float)
```

Updates `self._idle_threshold`. No timer restart needed — the next `_tick()` will use the new value.

### 4. App wiring in `_show_settings()`

After saving config to disk, call:

```python
self._state.update_intervals(
    work_interval_min=s["work_interval_min"],
    break_duration_min=s["break_duration_min"],
    dismiss_hide_min=s["dismiss_hide_min"],
)
self._idle.update_threshold(s["idle_threshold_sec"])
```

Same calls added to `_show_wizard()` after wizard completion.

### 5. SettingsWindow: Timer status card in Time tab

**Constructor change:** Accept optional `timer_info_cb` callable. If provided, start a 1-second QTimer that calls the callback and updates the display.

**New UI element:** A status card widget at the top of the time tab (above the sliders), containing:
- Emoji icon indicating current state
- State label (工作中 / 猫咪出现了 / 休息中 / 休息暂停 / 猫藏起来了 / 休息完成)
- Countdown text (e.g., "猫咪还有 25 分钟过来玩")
- Progress bar showing elapsed/total ratio
- Elapsed/total labels below the bar

**State-specific display:**

| State | Emoji | Color | Text |
|-------|-------|-------|------|
| WORKING | 🐱 | orange | 猫咪还有 X 分钟过来玩 |
| CAT_SHOW | 😺 | orange | 正在等待你休息... (no progress bar) |
| RESTING | 😴 | green | 还剩 X 分 X 秒 |
| RESTING_PAUSED | 🙀 | yellow | 检测到活动，休息计时暂停中... |
| CAT_HIDING | 🙈 | red | 猫咪 X 秒后再次出现 |
| REST_DONE | ✅ | — | 休息完成！(brief, no progress bar) |

The card is hidden when the state has no timer data to display.

### Timer behavior when settings change

| Changed setting | Current state | Behavior |
|----------------|--------------|----------|
| Work interval | WORKING | Immediate: elapsed preserved, remaining recalculated |
| Work interval | Any other | Takes effect next work cycle |
| Break duration | RESTING / RESTING_PAUSED | Current break finishes with old value, next break uses new |
| Break duration | Any other | Takes effect next break cycle |
| Dismiss hide | CAT_HIDING | Current hide finishes with old value, next hide uses new |
| Dismiss hide | Any other | Takes effect next hide cycle |
| Idle threshold | Any | Immediate (next tick picks up new value) |

## Files Changed

| File | Change |
|------|--------|
| `naughty_cat/state_machine.py` | Add `update_intervals()`, `timer_info()` |
| `naughty_cat/idle_detector.py` | Add `update_threshold()` |
| `naughty_cat/main.py` | Call `update_intervals()` and `update_threshold()` after settings save |
| `naughty_cat/ui/settings_window.py` | Accept `timer_info_cb`, add timer status card with 1s poll timer |

## Testing

- **Unit test `test_state_machine.py`**: Add tests for `update_intervals()` in WORKING state (elapsed preserved) and non-WORKING states (no immediate effect); test `timer_info()` returns correct data per state
- **Unit test `test_idle_detector.py`**: Add test for `update_threshold()`
- **Unit test `test_settings_window.py`**: Add test that timer display appears when callback is provided
- **Manual smoke test**: Open settings while working, change work interval, verify timer card updates immediately
