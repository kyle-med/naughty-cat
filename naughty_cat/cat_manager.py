import math
import random
from pathlib import Path
from PySide6.QtCore import (
    QObject, QTimer, Signal, QPoint, QRect, QSize, Property,
    QPropertyAnimation, QParallelAnimationGroup, QAbstractAnimation,
    QEasingCurve, Qt,
)
from PySide6.QtGui import QMovie, QPainter, QTransform
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QApplication, QGraphicsOpacityEffect,
)


class _CatWindow(QWidget):
    def __init__(self, gif_path: str, size: int, manager, index: int):
        super().__init__()
        self._manager = manager
        self._index = index
        self._angle = random.uniform(0, 2 * math.pi)
        self._speed = random.uniform(30, 80)
        self._rotation = 0.0

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._label = QLabel(self)
        self._label.setFixedSize(size, size)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setScaledContents(True)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)

        movie = QMovie(gif_path)
        movie.setScaledSize(self._label.size())
        self._label.setMovie(movie)
        movie.start()
        self._movie = movie

        layout.addWidget(self._label)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = random.randint(0, max(0, geo.width() - size))
            y = random.randint(0, max(0, geo.height() - size))
            self.move(x, y)

    def get_rotation(self) -> float:
        return self._rotation

    def set_rotation(self, value: float):
        self._rotation = value
        self.update()

    rotation = Property(float, get_rotation, set_rotation)

    def mousePressEvent(self, event):
        self._manager.dismiss_all()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        if self._rotation != 0.0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pivot = self.rect().center()
            t = QTransform()
            t.translate(pivot.x(), pivot.y())
            t.rotate(self._rotation)
            t.translate(-pivot.x(), -pivot.y())
            painter.setTransform(t)
        super().paintEvent(event)

    def move_step(self, dt_sec: float, screen_rect: QRect):
        dx = math.cos(self._angle) * self._speed * dt_sec
        dy = math.sin(self._angle) * self._speed * dt_sec
        new_x = self.x() + int(dx)
        new_y = self.y() + int(dy)

        if new_x < screen_rect.left() or new_x + self.width() > screen_rect.right():
            self._angle = math.pi - self._angle
            new_x = max(screen_rect.left(), min(new_x, screen_rect.right() - self.width()))
        if new_y < screen_rect.top() or new_y + self.height() > screen_rect.bottom():
            self._angle = -self._angle
            new_y = max(screen_rect.top(), min(new_y, screen_rect.bottom() - self.height()))

        self.move(new_x, new_y)

    def update_size(self, size: int):
        self.setFixedSize(size, size)
        self._label.setFixedSize(size, size)
        if self._movie:
            self._movie.setScaledSize(self._label.size())

    def animate_dismiss(self, callback):
        angle = random.uniform(0, 2 * math.pi)
        distance = 600 + random.uniform(0, 400)
        end_x = self.x() + int(math.cos(angle) * distance)
        end_y = self.y() + int(math.sin(angle) * distance)
        spin_degrees = random.choice([360, 540, 720])

        group = QParallelAnimationGroup(self)

        pos_anim = QPropertyAnimation(self, b"pos")
        pos_anim.setEndValue(QPoint(end_x, end_y))
        pos_anim.setDuration(600)
        pos_anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.InCubic))

        opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity)
        opacity_anim = QPropertyAnimation(opacity, b"opacity")
        opacity_anim.setEndValue(0.0)
        opacity_anim.setDuration(500)

        size_anim = QPropertyAnimation(self, b"size")
        size_anim.setEndValue(QSize(0, 0))
        size_anim.setDuration(600)
        size_anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.InCubic))

        rot_anim = QPropertyAnimation(self, b"rotation")
        rot_anim.setEndValue(float(spin_degrees))
        rot_anim.setDuration(600)
        rot_anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.Linear))

        group.addAnimation(pos_anim)
        group.addAnimation(opacity_anim)
        group.addAnimation(size_anim)
        group.addAnimation(rot_anim)

        group.finished.connect(self.hide)
        group.finished.connect(callback)
        group.finished.connect(lambda: group.deleteLater())
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


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
        self._pending_animations = 0

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
        if self._pending_animations > 0:
            return
        self._move_timer.stop()
        self._dir_change_timer.stop()
        if not self._windows:
            self.dismiss_requested.emit()
            return
        self._pending_animations = len([w for w in self._windows if w.isVisible()])
        if self._pending_animations == 0:
            self.dismiss_requested.emit()
            return
        for w in self._windows:
            if w.isVisible():
                w.animate_dismiss(self._on_animation_done)

    def remove_all(self):
        self._move_timer.stop()
        self._dir_change_timer.stop()
        self._pending_animations = 0
        for w in self._windows:
            w.close()
        self._windows.clear()

    def update_cats(self, count: int, size: int, active_cat_gifs: list[str]):
        if self._windows:
            self.spawn_cats(count, size, active_cat_gifs)

    def _on_animation_done(self):
        self._pending_animations -= 1
        if self._pending_animations <= 0:
            self._pending_animations = 0
            self.dismiss_requested.emit()

    def _move_cats(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_rect = screen.availableGeometry()
        dt = 0.1
        for w in self._windows:
            if w.isVisible():
                w.move_step(dt, screen_rect)

    def _randomize_directions(self):
        for w in self._windows:
            if random.random() < 0.5:
                w._angle = random.uniform(0, 2 * math.pi)
                w._speed = random.uniform(30, 80)
