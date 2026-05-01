from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QSlider, QPushButton, QFileDialog, QGroupBox, QScrollArea,
    QGridLayout, QFrame,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QMovie
from pathlib import Path


class _CatCard(QFrame):
    clicked = Signal()

    def __init__(self, name: str, gif_path: str, selected: bool, parent=None):
        super().__init__(parent)
        self._selected = selected
        self._name = name
        self.setFixedSize(100, 120)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(4)

        self._preview = QLabel()
        self._preview.setFixedSize(80, 72)
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setScaledContents(True)
        self._preview.setStyleSheet("background: transparent; border: none;")

        movie = QMovie(gif_path)
        movie.setScaledSize(QSize(80, 72))
        self._preview.setMovie(movie)
        movie.start()
        self._movie = movie

        layout.addWidget(self._preview, alignment=Qt.AlignCenter)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(
            "font-size: 11px; color: #1C1C1E; border: none; background: transparent;"
        )
        layout.addWidget(name_label)

    def _update_style(self):
        if self._selected:
            self.setStyleSheet("""
                _CatCard {
                    background: #FFFFFF;
                    border: 2px solid #007AFF;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                _CatCard {
                    background: #FFFFFF;
                    border: 2px solid rgba(0,0,0,0.06);
                    border-radius: 12px;
                }
                _CatCard:hover {
                    border-color: rgba(0,0,0,0.15);
                }
            """)

    @property
    def selected(self):
        return self._selected

    def toggle(self):
        self._selected = not self._selected
        self._update_style()

    def mousePressEvent(self, event):
        self.toggle()
        self.clicked.emit()
        super().mousePressEvent(event)


class CatConfigPanel(QWidget):
    selection_changed = Signal()

    def __init__(
        self,
        cats: list[dict],
        active_names: list[str],
        count: int,
        size: int,
        parent=None,
    ):
        super().__init__(parent)
        self._cats = cats
        self._cards: list[_CatCard] = []

        layout = QVBoxLayout(self)

        # Cat selection as scrollable cards
        cat_group = QGroupBox("选择猫咪")
        cat_layout = QVBoxLayout(cat_group)

        self._grid = QGridLayout()
        self._grid.setSpacing(8)

        assets_dir = Path(__file__).parent.parent / "assets" / "cats"

        for i, cat in enumerate(cats):
            gif_path = cat["file"]
            if not Path(gif_path).is_absolute():
                gif_path = str(assets_dir / gif_path)
            is_selected = cat["name"] in active_names
            card = _CatCard(cat["name"], gif_path, is_selected)
            card.clicked.connect(self.selection_changed.emit)
            self._cards.append(card)
            self._grid.addWidget(card, i // 2, i % 2)

        cat_layout.addLayout(self._grid)

        self._import_btn = QPushButton("导入猫咪 (GIF/APNG)...")
        self._import_btn.clicked.connect(self._import_cat)
        cat_layout.addWidget(self._import_btn)

        # Wrap cat group in scroll area so it never overflows
        scroll = QScrollArea()
        scroll.setWidget(cat_group)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        layout.addWidget(scroll, 1)

        # Count and size
        settings_group = QGroupBox("猫咪设置")
        settings_layout = QVBoxLayout(settings_group)

        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("猫咪数量"))
        self.cat_count_spin = QSpinBox()
        self.cat_count_spin.setRange(1, 10)
        self.cat_count_spin.setValue(count)
        count_layout.addWidget(self.cat_count_spin)
        settings_layout.addLayout(count_layout)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("猫咪大小"))
        self.cat_size_slider = QSlider(Qt.Horizontal)
        self.cat_size_slider.setRange(30, 300)
        self.cat_size_slider.setValue(size)
        self.cat_size_label = QLabel(str(size))
        self.cat_size_slider.valueChanged.connect(
            lambda v: self.cat_size_label.setText(str(v))
        )
        size_layout.addWidget(self.cat_size_slider)
        size_layout.addWidget(self.cat_size_label)
        settings_layout.addLayout(size_layout)

        layout.addWidget(settings_group)

    def get_active_cats(self) -> list[str]:
        return [card._name for card in self._cards if card.selected]

    def get_cat_count(self) -> int:
        return self.cat_count_spin.value()

    def get_cat_size(self) -> int:
        return self.cat_size_slider.value()

    def _import_cat(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入猫咪", "",
            "Images (*.gif *.apng *.png);;All Files (*)"
        )
        if not path:
            return
        name = Path(path).stem
        self._cats.append({"name": name, "file": path, "builtin": False})
        card = _CatCard(name, str(path), True)
        card.clicked.connect(self.selection_changed.emit)
        self._cards.append(card)
        idx = len(self._cards) - 1
        self._grid.addWidget(card, idx // 2, idx % 2)

    def get_cats(self) -> list[dict]:
        return self._cats
