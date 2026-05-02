"""iOS Minimalist Premium design system for Naughty Cat."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSlider, QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor

APP_STYLESHEET = """
/* ---- iOS Minimalist Premium -- Naughty Cat ---- */

/* --- Base --- */
QDialog, QWizard {
    background: #F2F2F7;
}
* {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}

/* --- GroupBox (cards) --- */
QGroupBox {
    background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px 16px 14px 16px;
    font-size: 12px;
    font-weight: 600;
    color: #8E8E93;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 4px;
}

/* --- PushButton (primary) --- */
QPushButton {
    background: #007AFF;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 500;
    min-height: 20px;
}
QPushButton:hover {
    background: #0062CC;
}
QPushButton:pressed {
    background: #004999;
}
QPushButton:disabled {
    background: #B0B0B0;
}

/* --- Slider (horizontal) --- */
QSlider::groove:horizontal {
    height: 4px;
    background: #E5E5EA;
    border-radius: 2px;
    border: none;
}
QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 1px solid #D1D1D6;
    width: 24px;
    height: 24px;
    margin: -10px 0;
    border-radius: 12px;
}
QSlider::handle:horizontal:hover {
    border-color: #007AFF;
    background: #F2F7FF;
}
QSlider::sub-page:horizontal {
    background: #007AFF;
    border-radius: 2px;
}

/* --- CheckBox --- */
QCheckBox {
    spacing: 10px;
    font-size: 14px;
    color: #1C1C1E;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #D1D1D6;
    border-radius: 5px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked {
    background: #007AFF;
    border-color: #007AFF;
}
QCheckBox::indicator:hover {
    border-color: #007AFF;
}

/* --- TabWidget --- */
QTabWidget::pane {
    background: #F2F2F7;
    border: none;
    border-top: 1px solid #E5E5EA;
}
QTabBar::tab {
    background: transparent;
    color: #8E8E93;
    font-size: 13px;
    font-weight: 500;
    padding: 10px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    min-width: 50px;
}
QTabBar::tab:selected {
    color: #007AFF;
    border-bottom: 2px solid #007AFF;
}
QTabBar::tab:hover {
    color: #1C1C1E;
}

/* --- Label --- */
QLabel {
    color: #1C1C1E;
    font-size: 14px;
    background: transparent;
}

/* --- SpinBox --- */
QSpinBox {
    background: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 14px;
    min-height: 24px;
    color: #1C1C1E;
}
QSpinBox:focus {
    border-color: #007AFF;
}

/* --- QFormLayout row labels --- */
QFormLayout > QLabel {
    color: #1C1C1E;
    font-size: 14px;
    font-weight: 500;
}

/* --- QMessageBox --- */
QMessageBox {
    background: #F2F2F7;
}
QMessageBox QLabel {
    color: #1C1C1E;
    font-size: 14px;
}
"""


def make_slider_row(lo: int, hi: int, default: int, unit: str):
    """Shared slider factory with proper spacing.

    Returns (slider, container_widget).
    Caller uses slider.value() for reading; container_widget for layout insertion.
    """
    w = QWidget()
    layout = QHBoxLayout(w)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    slider = QSlider(Qt.Horizontal)
    slider.setRange(lo, hi)
    slider.setValue(default)

    label = QLabel(f"{default} {unit}")
    label.setMinimumWidth(50)
    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    label.setStyleSheet("color: #8E8E93; font-size: 13px;")

    slider.valueChanged.connect(lambda v, l=label, u=unit: l.setText(f"{v} {u}"))
    layout.addWidget(slider, 1)
    layout.addWidget(label)

    return slider, w


def card_shadow(widget: QWidget):
    """Apply iOS-style subtle drop shadow to a widget."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(20)
    shadow.setOffset(0, 4)
    shadow.setColor(QColor(0, 0, 0, 25))
    widget.setGraphicsEffect(shadow)
