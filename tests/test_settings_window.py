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
