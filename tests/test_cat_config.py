from PySide6.QtWidgets import QApplication
from naughty_cat.ui.cat_config import CatConfigPanel


def test_cat_config_initializes_with_cats(qtbot):
    cats = [
        {"name": "波仔", "file": "orange_cat.gif", "builtin": True},
        {"name": "蓝猫", "file": "blue_cat.gif", "builtin": True},
    ]
    active = ["波仔"]
    panel = CatConfigPanel(cats, active, count=2, size=100)
    qtbot.addWidget(panel)

    assert panel.cat_count_spin.value() == 2
    assert panel.cat_size_slider.value() == 100


def test_cat_config_import_button_exists(qtbot):
    cats = [{"name": "波仔", "file": "orange_cat.gif", "builtin": True}]
    panel = CatConfigPanel(cats, ["波仔"], count=1, size=100)
    qtbot.addWidget(panel)
    assert panel._import_btn is not None
