from pathlib import Path
from PySide6.QtCore import QCoreApplication
from naughty_cat.sound_player import SoundPlayer


def test_sound_player_initial_state():
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    assert player.volume() == 30
    assert player.enabled is True


def test_set_volume_clamps():
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    player.set_volume(50)
    assert player.volume() == 50
    player.set_volume(-10)
    assert player.volume() == 0
    player.set_volume(200)
    assert player.volume() == 100


def test_set_enabled():
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    player.set_enabled(False)
    assert player.enabled is False
    player.set_enabled(True)
    assert player.enabled is True


def test_play_does_not_crash_when_disabled(qtbot):
    app = QCoreApplication.instance() or QCoreApplication([])
    player = SoundPlayer()
    player.set_enabled(False)
    # Should not raise
    player.play("meow1.mp3")
