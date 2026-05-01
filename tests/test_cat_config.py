from PySide6.QtWidgets import QApplication
from naughty_cat.ui.cat_config import CatConfigPanel


def test_cat_config_initializes_with_cats(qtbot):
    cats = [
        {"name": "波仔", "file": "波仔.gif", "builtin": True},
        {"name": "咣当", "file": "咣当.gif", "builtin": True},
    ]
    active = ["波仔"]
    panel = CatConfigPanel(cats, active, count=2, size=100)
    qtbot.addWidget(panel)

    assert panel.cat_count_spin.value() == 2
    assert panel.cat_size_slider.value() == 100


def test_cat_config_import_button_exists(qtbot):
    cats = [{"name": "波仔", "file": "波仔.gif", "builtin": True}]
    panel = CatConfigPanel(cats, ["波仔"], count=1, size=100)
    qtbot.addWidget(panel)
    assert panel._import_btn is not None


def test_cat_config_get_active_cats(qtbot):
    cats = [
        {"name": "波仔", "file": "波仔.gif", "builtin": True},
        {"name": "咣当", "file": "咣当.gif", "builtin": True},
    ]
    active = ["波仔"]
    panel = CatConfigPanel(cats, active, count=2, size=100)
    qtbot.addWidget(panel)
    # Initially only 波仔 is active
    assert panel.get_active_cats() == ["波仔"]
