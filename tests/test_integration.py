from PySide6.QtWidgets import QApplication
from naughty_cat.config_store import ConfigStore
from naughty_cat.idle_detector import IdleDetector
from naughty_cat.sound_player import SoundPlayer
from naughty_cat.state_machine import StateMachine, Event, State
from naughty_cat.cat_manager import CatManager
from naughty_cat.tray_icon import TrayIcon
from naughty_cat.ui.break_done_toast import BreakDoneToast
from naughty_cat.ui.settings_window import SettingsWindow
from naughty_cat.ui.welcome_wizard import WelcomeWizard


def test_full_workflow_imports(qtbot):
    """Sanity check: all modules import and can be instantiated."""
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp()) / "config.json"
    config = ConfigStore(tmp)
    assert config is not None

    idle = IdleDetector()
    assert idle is not None

    sound = SoundPlayer()
    assert sound is not None

    sm = StateMachine(50, 5, 5, 1)
    assert sm.current_state == State.WORKING

    cats = CatManager()
    assert cats.cat_count == 0

    tray = TrayIcon()
    assert tray is not None

    toast = BreakDoneToast()
    assert toast is not None
