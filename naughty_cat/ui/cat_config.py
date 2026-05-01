from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
    QSpinBox, QSlider, QPushButton, QFileDialog, QGroupBox, QScrollArea,
)
from PySide6.QtCore import Qt


class CatConfigPanel(QWidget):
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
        self._checkboxes: dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)

        # Cat selection
        cat_group = QGroupBox("选择猫咪")
        cat_layout = QVBoxLayout(cat_group)

        for cat in cats:
            cb = QCheckBox(cat["name"])
            cb.setChecked(cat["name"] in active_names)
            cb.toggled.connect(self._on_selection_changed)
            self._checkboxes[cat["name"]] = cb
            cat_layout.addWidget(cb)

        self._import_btn = QPushButton("导入猫咪 (GIF/APNG)...")
        self._import_btn.clicked.connect(self._import_cat)
        cat_layout.addWidget(self._import_btn)

        layout.addWidget(cat_group)

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
        layout.addStretch()

    def get_active_cats(self) -> list[str]:
        return [name for name, cb in self._checkboxes.items() if cb.isChecked()]

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
        from pathlib import Path
        name = Path(path).stem
        self._cats.append({"name": name, "file": path, "builtin": False})
        cb = QCheckBox(name)
        cb.setChecked(True)
        cb.toggled.connect(self._on_selection_changed)
        self._checkboxes[name] = cb
        # Insert before the import button
        cat_layout = self._import_btn.parent().layout()
        if cat_layout:
            cat_layout.insertWidget(cat_layout.count() - 1, cb)

    def get_cats(self) -> list[dict]:
        return self._cats

    def _on_selection_changed(self):
        pass
