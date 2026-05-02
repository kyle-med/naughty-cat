import sys
import os
import ctypes
from ctypes import wintypes
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal
from PySide6.QtCore import QAbstractNativeEventFilter

from naughty_cat.config_store import ConfigStore
from naughty_cat.idle_detector import IdleDetector
from naughty_cat.sound_player import SoundPlayer
from naughty_cat.state_machine import StateMachine, State, Event
from naughty_cat.cat_manager import CatManager
from naughty_cat.tray_icon import TrayIcon
from naughty_cat.ui.welcome_wizard import WelcomeWizard
from naughty_cat.ui.settings_window import SettingsWindow
from naughty_cat.ui.break_done_toast import BreakDoneToast
from naughty_cat.ui.style import APP_STYLESHEET

WM_POWERBROADCAST = 0x0218
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMESUSPEND = 0x0007


class _WinPowerFilter(QObject, QAbstractNativeEventFilter):
    suspend = Signal()
    resume = Signal()

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            msg = ctypes.cast(
                ctypes.c_void_p(int(message)), ctypes.POINTER(wintypes.MSG)
            ).contents
            if msg.message == WM_POWERBROADCAST:
                if msg.wParam == PBT_APMSUSPEND:
                    self.suspend.emit()
                elif msg.wParam == PBT_APMRESUMESUSPEND:
                    self.resume.emit()
        return False, 0


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
        self._sound = SoundPlayer(
            custom_sounds=self._config.settings.get("custom_sounds", [])
        )
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

        self._power_filter = _WinPowerFilter()

        self._wire()

    def _wire(self):
        # State changes drive cat visibility
        self._state.state_changed.connect(self._on_state_changed)

        # Idle detection feeds state machine
        self._idle.became_idle.connect(lambda: self._state.transition(Event.IDLE_DETECTED))
        self._idle.idle_seconds_changed.connect(self._on_idle_seconds_changed)

        # Cat dismiss button
        self._cats.dismiss_requested.connect(lambda: self._state.transition(Event.DISMISS_CLICKED))

        # Tray actions
        self._tray.summon_requested.connect(lambda: self._state.transition(Event.MANUAL_SUMMON))
        self._tray.pause_toggled.connect(self._on_pause_toggle)
        self._tray.settings_requested.connect(self._show_settings)
        self._tray.quit_requested.connect(self._quit)

        # Lid close / open → auto pause / resume
        self._power_filter.suspend.connect(
            lambda: self._state.pause() if not self._state.is_paused else None
        )
        self._power_filter.resume.connect(
            lambda: self._state.resume() if self._state.is_paused else None
        )

    def start(self):
        if self._config.settings["first_run"]:
            self._show_wizard()

        _apply_auto_start(self._config.settings["auto_start"])
        QApplication.instance().installNativeEventFilter(self._power_filter)
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
            self._sound.play("meow.mp3")

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

    def _on_pause_button_toggle(self):
        if self._state.is_paused:
            self._state.resume()
        else:
            self._state.pause()
        self._tray.set_paused(self._state.is_paused)

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

    def _show_settings(self):
        if self._settings_win and self._settings_win.isVisible():
            self._settings_win.raise_()
            return
        self._settings_win = SettingsWindow(
            self._config.settings["cats"],
            self._config.settings,
            timer_info_cb=self._state.timer_info,
            is_paused_cb=lambda: self._state.is_paused,
            toggle_pause_cb=self._on_pause_button_toggle,
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
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    font = app.font()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    naughty = App()
    naughty.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
