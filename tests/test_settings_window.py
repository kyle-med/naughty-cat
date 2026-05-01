from naughty_cat.ui.settings_window import SettingsWindow


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
