import math
import random
from pathlib import Path
from PySide6.QtCore import QObject, QTimer, Signal, QPoint, QRect
from PySide6.QtGui import QScreen, QMovie, QMouseEvent
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication
from PySide6.QtCore import Qt


class _CatWindow(QWidget):
    def __init__(self, gif_path: str, size: int, manager, index: int):
        super().__init__()
        self._manager = manager
        self._index = index
        self._angle = random.uniform(0, 2 * math.pi)
        self._speed = random.uniform(80, 200)

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(size, size)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._label = QLabel(self)
        self._label.setFixedSize(size, size - 24)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setScaledContents(True)

        movie = QMovie(gif_path)
        movie.setScaledSize(self._label.size())
        self._label.setMovie(movie)
        movie.start()
        self._movie = movie

        dismiss_btn = QPushButton("驱赶 ×", self)
        dismiss_btn.setFixedHeight(20)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                border: 1px solid rgba(255,255,255,0.25);
                border-radius: 4px;
                color: rgba(255,255,255,0.8);
                font-size: 10px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        dismiss_btn.clicked.connect(self._manager.dismiss_all)

        layout.addWidget(self._label)
        layout.addWidget(dismiss_btn, alignment=Qt.AlignCenter)

        # Start at random position
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = random.randint(0, max(0, geo.width() - size))
            y = random.randint(0, max(0, geo.height() - size))
            self.move(x, y)

    def move_step(self, dt_sec: float, screen_rect: QRect):
        dx = math.cos(self._angle) * self._speed * dt_sec
        dy = math.sin(self._angle) * self._speed * dt_sec
        new_x = self.x() + int(dx)
        new_y = self.y() + int(dy)

        # Bounce off edges
        if new_x < screen_rect.left() or new_x + self.width() > screen_rect.right():
            self._angle = math.pi - self._angle
            new_x = max(screen_rect.left(), min(new_x, screen_rect.right() - self.width()))
        if new_y < screen_rect.top() or new_y + self.height() > screen_rect.bottom():
            self._angle = -self._angle
            new_y = max(screen_rect.top(), min(new_y, screen_rect.bottom() - self.height()))

        self.move(new_x, new_y)

    def update_size(self, size: int):
        self.setFixedSize(size, size)
        self._label.setFixedSize(size, size - 24)
        if self._movie:
            self._movie.setScaledSize(self._label.size())


class CatManager(QObject):
    dismiss_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._windows: list[_CatWindow] = []
        self._move_timer = QTimer(self)
        self._move_timer.setInterval(100)
        self._move_timer.timeout.connect(self._move_cats)
        self._dir_change_timer = QTimer(self)
        self._dir_change_timer.setInterval(3000)
        self._dir_change_timer.timeout.connect(self._randomize_directions)

        self._cats_dir = Path(__file__).parent / "assets" / "cats"

    @property
    def cat_count(self) -> int:
        return len(self._windows)

    def spawn_cats(self, count: int, size: int, active_cat_gifs: list[str]):
        self.remove_all()
        gifs = [str(self._cats_dir / g) for g in active_cat_gifs]
        if not gifs:
            return

        for i in range(count):
            gif = gifs[i % len(gifs)]
            win = _CatWindow(gif, size, self, i)
            win.show()
            self._windows.append(win)

        self._move_timer.start()
        self._dir_change_timer.start()

    def dismiss_all(self):
        self._move_timer.stop()
        self._dir_change_timer.stop()
        for w in self._windows:
            w.hide()
        self.dismiss_requested.emit()

    def remove_all(self):
        self._move_timer.stop()
        self._dir_change_timer.stop()
        for w in self._windows:
            w.close()
        self._windows.clear()

    def update_cats(self, count: int, size: int, active_cat_gifs: list[str]):
        if self._windows:
            self.spawn_cats(count, size, active_cat_gifs)

    def _move_cats(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_rect = screen.availableGeometry()
        dt = 0.1  # 100ms
        for w in self._windows:
            if w.isVisible():
                w.move_step(dt, screen_rect)

    def _randomize_directions(self):
        for w in self._windows:
            if random.random() < 0.5:
                w._angle = random.uniform(0, 2 * math.pi)
                w._speed = random.uniform(80, 200)
