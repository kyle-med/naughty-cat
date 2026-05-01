from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QApplication,
    QGraphicsDropShadowEffect,
)


class BreakDoneToast(QWidget):
    acknowledged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(260, 120)

        self.setStyleSheet("""
            BreakDoneToast {
                background: #FFFFFF;
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        label = QLabel("猫咪出去玩了！🐱")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            "font-size: 14px; font-weight: 500; color: #1C1C1E; border: none;"
        )
        layout.addWidget(label)

        self._btn = QPushButton("知道了")
        self._btn.clicked.connect(self._on_acknowledge)
        layout.addWidget(self._btn, alignment=Qt.AlignCenter)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - 280, geo.bottom() - 130)

    def _on_acknowledge(self):
        self.acknowledged.emit()
        self.close()
