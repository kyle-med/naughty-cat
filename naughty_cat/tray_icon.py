from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


_ICONS_DIR = Path(__file__).parent / "assets" / "icons"


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu for Naughty Cat."""

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
            self.setIcon(
                QApplication.style().standardIcon(
                    QStyle.StandardPixmap.SP_ComputerIcon
                )
            )

        self._summon_action = QAction("手动召唤猫咪")
        self._summon_action.triggered.connect(self.summon_requested.emit)
        self._menu.addAction(self._summon_action)

        self._pause_action = QAction("暂停提醒")
        self._pause_action.triggered.connect(self._on_pause_toggle)
        self._menu.addAction(self._pause_action)

        self._menu.addSeparator()

        self._settings_action = QAction("设置")
        self._settings_action.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(self._settings_action)

        self._about_action = QAction("关于")
        self._menu.addAction(self._about_action)

        self._menu.addSeparator()

        self._quit_action = QAction("退出")
        self._quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(self._quit_action)

        self.setContextMenu(self._menu)
        self.setToolTip("Naughty Cat")

        self.activated.connect(self._on_activated)

    def set_paused(self, paused: bool):
        """Update icon and pause-action text to reflect paused state."""
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
