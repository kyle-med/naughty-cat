from pathlib import Path
from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class SoundPlayer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._volume = 30
        self.enabled = True
        self._audio.setVolume(self._volume / 100.0)
        self._sound_dir = Path(__file__).parent / "assets" / "sounds"

    def volume(self) -> int:
        return self._volume

    def set_volume(self, vol: int):
        self._volume = max(0, min(100, vol))
        self._audio.setVolume(self._volume / 100.0)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def play(self, name: str):
        if not self.enabled:
            return
        path = self._sound_dir / name
        if path.exists():
            self._player.setSource(QUrl.fromLocalFile(str(path)))
            self._player.play()
