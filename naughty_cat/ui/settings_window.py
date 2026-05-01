from PySide6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QCheckBox, QPushButton, QSpinBox, QFormLayout, QGroupBox, QWidget
)
from PySide6.QtCore import Qt
from naughty_cat.ui.cat_config import CatConfigPanel


class SettingsWindow(QDialog):
    def __init__(self, cats: list[dict], settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Naughty Cat 设置")
        self.setMinimumSize(420, 380)

        self._slider_wrappers: list[QWidget] = []
        layout = QVBoxLayout(self)
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # Tab 1: Cats
        self._cat_panel = CatConfigPanel(
            cats, settings.get("active_cats", []),
            count=settings.get("cat_count", 2),
            size=settings.get("cat_size", 100)
        )
        self._tab_widget.addTab(self._cat_panel, "🐱 猫咪")

        # Tab 2: Time
        time_tab = QWidget()
        time_layout = QFormLayout(time_tab)

        self._work_slider = self._make_slider(15, 120, settings.get("work_interval_min", 50), "分钟")
        self._break_slider = self._make_slider(1, 30, settings.get("break_duration_min", 5), "分钟")
        self._idle_slider = self._make_slider(2, 30, settings.get("idle_threshold_sec", 5), "秒")
        self._dismiss_slider = self._make_slider(1, 30, settings.get("dismiss_hide_min", 1), "分钟")

        time_layout.addRow("工作间隔", self._work_slider)
        time_layout.addRow("休息时长", self._break_slider)
        time_layout.addRow("空闲检测", self._idle_slider)
        time_layout.addRow("驱赶隐藏", self._dismiss_slider)
        self._tab_widget.addTab(time_tab, "⏰ 时间")

        # Tab 3: Sound
        sound_tab = QWidget()
        sound_layout = QVBoxLayout(sound_tab)

        self._sound_enabled_cb = QCheckBox("启用音效")
        self._sound_enabled_cb.setChecked(settings.get("sound_enabled", True))
        sound_layout.addWidget(self._sound_enabled_cb)

        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("音量"))
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(settings.get("sound_volume", 30))
        self._volume_label = QLabel(str(self._volume_slider.value()))
        self._volume_slider.valueChanged.connect(
            lambda v: self._volume_label.setText(str(v))
        )
        vol_layout.addWidget(self._volume_slider)
        vol_layout.addWidget(self._volume_label)
        sound_layout.addLayout(vol_layout)

        import_btn = QPushButton("导入自定义音效...")
        sound_layout.addWidget(import_btn)
        sound_layout.addStretch()
        self._tab_widget.addTab(sound_tab, "🔊 音效")

        # Tab 4: General
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        self._auto_start_cb = QCheckBox("开机自动启动")
        self._auto_start_cb.setChecked(settings.get("auto_start", True))
        general_layout.addWidget(self._auto_start_cb)

        general_layout.addStretch()

        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel("Naughty Cat v0.1.0"))
        about_layout.addWidget(QLabel("一个用猫咪提醒你休息的小工具"))
        general_layout.addWidget(about_group)

        self._tab_widget.addTab(general_tab, "⚙️ 通用")

        # OK/Cancel buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("保存")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_settings(self) -> dict:
        return {
            "active_cats": self._cat_panel.get_active_cats(),
            "cat_count": self._cat_panel.get_cat_count(),
            "cat_size": self._cat_panel.get_cat_size(),
            "work_interval_min": self._work_slider.value(),
            "break_duration_min": self._break_slider.value(),
            "idle_threshold_sec": self._idle_slider.value(),
            "dismiss_hide_min": self._dismiss_slider.value(),
            "sound_enabled": self._sound_enabled_cb.isChecked(),
            "sound_volume": self._volume_slider.value(),
            "auto_start": self._auto_start_cb.isChecked(),
        }

    def _make_slider(self, lo, hi, default, unit):
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(default)
        label = QLabel(f"{default} {unit}")
        slider.valueChanged.connect(lambda v, l=label, u=unit: l.setText(f"{v} {u}"))
        layout.addWidget(slider)
        layout.addWidget(label)
        self._slider_wrappers.append(w)
        return slider
