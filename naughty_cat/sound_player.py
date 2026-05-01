from pathlib import Path
from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class SoundPlayer(QObject):
    def __init__(self, custom_sounds: list[str] | None = None, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._volume = 30
        self.enabled = True
        self._audio.setVolume(self._volume / 100.0)
        self._builtin_dir = Path(__file__).parent / "assets" / "sounds"
        self._custom_paths: list[str] = custom_sounds or []

    def volume(self) -> int:
        return self._volume

    def set_volume(self, vol: int):
        self._volume = max(0, min(100, vol))
        self._audio.setVolume(self._volume / 100.0)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_custom_sounds(self, paths: list[str]):
        self._custom_paths = paths

    def play(self, name: str):
        if not self.enabled:
            return
        # Try built-in first
        path = self._builtin_dir / name
        if not path.exists():
            # Try custom paths
            path = None
            for cp in self._custom_paths:
                p = Path(cp)
                if p.name == name or str(p) == name:
                    path = p
                    break
            if path is None and Path(name).exists():
                path = Path(name)
        if path and path.exists():
            self._player.setSource(QUrl.fromLocalFile(str(path)))
            self._player.play()
