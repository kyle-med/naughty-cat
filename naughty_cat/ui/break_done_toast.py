from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
)


class BreakDoneToast(QWidget):
    acknowledged = Signal()

    def __init__(self, auto_dismiss_ms=30000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(240, 100)

        self.setStyleSheet("""
            QWidget {
                background: #2d2d3f;
                border: 1px solid #f0a040;
                border-radius: 12px;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background: #f0a040;
                border: none;
                border-radius: 6px;
                padding: 4px 16px;
                color: #1a1a2e;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #f5b850;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("猫咪出去玩了！\U0001f431")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self._btn = QPushButton("知道了")
        self._btn.clicked.connect(self._on_acknowledge)
        layout.addWidget(self._btn, alignment=Qt.AlignCenter)

        # Position bottom-right
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - 260, geo.bottom() - 120)

        if auto_dismiss_ms > 0:
            QTimer.singleShot(auto_dismiss_ms, self._on_acknowledge)

    def _on_acknowledge(self):
        self.acknowledged.emit()
        self.close()
