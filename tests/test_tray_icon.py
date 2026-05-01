from PySide6.QtWidgets import QApplication, QMenu
from naughty_cat.tray_icon import TrayIcon


def test_tray_icon_initializes(qtbot):
    app = QApplication.instance() or QApplication([])
    tray = TrayIcon()
    assert tray._menu is not None


def test_tray_menu_has_items(qtbot):
    tray = TrayIcon()
    actions = tray._menu.actions()
    action_texts = [a.text() for a in actions if a.text()]
    assert any("设置" in t for t in action_texts)
    assert any("退出" in t for t in action_texts)
