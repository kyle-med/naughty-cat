import ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject, QTimer, Signal

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def _get_idle_seconds() -> float:
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    return (kernel32.GetTickCount() - lii.dwTime) / 1000.0


class IdleDetector(QObject):
    idle_seconds_changed = Signal(float)
    became_idle = Signal()

    def __init__(self, check_interval_ms=500, idle_threshold_sec=5, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(check_interval_ms)
        self._timer.timeout.connect(self._tick)
        self._idle_threshold = idle_threshold_sec
        self._was_idle = False

    def start(self):
        self._was_idle = False
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def update_threshold(self, idle_threshold_sec: float):
        self._idle_threshold = idle_threshold_sec

    def _tick(self):
        secs = _get_idle_seconds()
        self.idle_seconds_changed.emit(secs)
        is_idle = secs >= self._idle_threshold
        if is_idle and not self._was_idle:
            self._was_idle = True
            self.became_idle.emit()
        elif not is_idle:
            self._was_idle = False
