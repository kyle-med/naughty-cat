from PySide6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QCheckBox, QPushButton, QSpinBox, QFormLayout, QGroupBox, QWidget,
    QFileDialog, QFrame
)
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from naughty_cat.ui.cat_config import CatConfigPanel
from naughty_cat.ui.style import make_slider_row
from naughty_cat.state_machine import State


class SettingsWindow(QDialog):
    def __init__(self, cats: list[dict], settings: dict, timer_info_cb=None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Naughty Cat 设置")
        self.setMinimumSize(480, 460)

        self._timer_info_cb = timer_info_cb

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
        time_layout = QVBoxLayout(time_tab)

        # Timer status card
        self._timer_status_card = self._build_timer_status_card()
        time_layout.addWidget(self._timer_status_card)

        form_layout = QFormLayout()
        self._work_slider, work_row = make_slider_row(
            3, 120, settings.get("work_interval_min", 50), "分钟")
        self._break_slider, break_row = make_slider_row(
            1, 30, settings.get("break_duration_min", 5), "分钟")
        self._idle_slider, idle_row = make_slider_row(
            2, 30, settings.get("idle_threshold_sec", 5), "秒")
        self._dismiss_slider, dismiss_row = make_slider_row(
            1, 30, settings.get("dismiss_hide_min", 1), "分钟")

        form_layout.addRow("工作间隔", work_row)
        form_layout.addRow("休息时长", break_row)
        form_layout.addRow("空闲检测", idle_row)
        form_layout.addRow("驱赶隐藏", dismiss_row)
        time_layout.addLayout(form_layout)
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

        self._imported_sounds = list(settings.get("custom_sounds", []))
        self._sound_list_label = QLabel()
        self._update_sound_list_label()
        sound_layout.addWidget(self._sound_list_label)

        self._sound_import_btn = QPushButton("导入自定义音效...")
        self._sound_import_btn.clicked.connect(self._import_sound)
        sound_layout.addWidget(self._sound_import_btn)
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

        # Start poll timer if callback provided
        self._poll_timer = None
        if self._timer_info_cb:
            self._refresh_timer_display()
            self._poll_timer = QTimer(self)
            self._poll_timer.setInterval(1000)
            self._poll_timer.timeout.connect(self._refresh_timer_display)
            self._poll_timer.start()

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
            "custom_sounds": self._imported_sounds,
            "auto_start": self._auto_start_cb.isChecked(),
        }

    def _build_timer_status_card(self):
        card = QFrame()
        card.setObjectName("timerStatusCard")
        card.setStyleSheet("""
            QFrame#timerStatusCard {
                background: #3d3d5c;
                border-radius: 10px;
                padding: 12px 16px;
            }
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)

        self._timer_emoji = QLabel()
        self._timer_emoji.setStyleSheet("font-size: 28px;")
        card_layout.addWidget(self._timer_emoji)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self._timer_state_label = QLabel()
        self._timer_state_label.setStyleSheet("color: #888; font-size: 11px;")
        info_layout.addWidget(self._timer_state_label)

        self._timer_countdown = QLabel()
        self._timer_countdown.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self._timer_countdown)

        # Progress bar
        self._timer_progress_bg = QWidget()
        self._timer_progress_bg.setFixedHeight(6)
        self._timer_progress_bg.setStyleSheet(
            "background: #2a2a3f; border-radius: 3px;")
        self._timer_progress_fill = QWidget(self._timer_progress_bg)
        self._timer_progress_fill.setFixedHeight(6)
        self._timer_progress_fill.setStyleSheet(
            "background: #f0a040; border-radius: 3px;")

        info_layout.addWidget(self._timer_progress_bg)

        info_layout.addStretch()
        card_layout.addLayout(info_layout, 1)
        card.setVisible(False)
        return card

    def _refresh_timer_display(self):
        if not self._timer_info_cb:
            return
        info = self._timer_info_cb()
        self._timer_status_card.setVisible(True)
        state = info["state"]
        remaining_ms = info["remaining_ms"]
        total_ms = info["total_ms"]
        progress = max(0.0, min(1.0, 1.0 - remaining_ms / total_ms)) if remaining_ms is not None and total_ms else 0.0

        if state == State.WORKING:
            remaining_min = remaining_ms / 60000
            self._timer_emoji.setText("🐱")
            self._timer_state_label.setText("当前状态 · 工作中")
            self._timer_countdown.setText(
                f"猫咪还有 {remaining_min:.0f} 分钟过来玩")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #f0a040;")
            self._timer_progress_fill.setStyleSheet(
                "background: #f0a040; border-radius: 3px;")
        elif state == State.CAT_SHOW:
            self._timer_emoji.setText("😺")
            self._timer_state_label.setText("当前状态 · 猫咪出现了！")
            self._timer_countdown.setText("正在等待你休息...")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #f5b860;")
            progress = 0.0
        elif state == State.RESTING:
            remaining_min = remaining_ms / 60000
            self._timer_emoji.setText("😴")
            self._timer_state_label.setText("当前状态 · 休息中")
            self._timer_countdown.setText(
                f"还剩 {remaining_min:.0f} 分钟")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #5cba80;")
            self._timer_progress_fill.setStyleSheet(
                "background: #5cba80; border-radius: 3px;")
        elif state == State.RESTING_PAUSED:
            self._timer_emoji.setText("🙀")
            self._timer_state_label.setText("当前状态 · 休息暂停")
            self._timer_countdown.setText("检测到活动，休息计时暂停中...")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #d0a050;")
            self._timer_progress_fill.setStyleSheet(
                "background: #d0a050; border-radius: 3px;")
        elif state == State.CAT_HIDING:
            remaining_sec = remaining_ms / 1000
            self._timer_emoji.setText("🙈")
            self._timer_state_label.setText("当前状态 · 猫藏起来了")
            self._timer_countdown.setText(
                f"猫咪 {remaining_sec:.0f} 秒后再次出现")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #d08060;")
            self._timer_progress_fill.setStyleSheet(
                "background: #d08060; border-radius: 3px;")
        elif state == State.REST_DONE:
            self._timer_emoji.setText("✅")
            self._timer_state_label.setText("当前状态 · 休息完成！")
            self._timer_countdown.setText("点击「知道了」继续工作")
            self._timer_countdown.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #5cb85c;")
            progress = 0.0
        else:
            self._timer_status_card.setVisible(False)
            return

        # Update progress bar width
        bg_width = self._timer_progress_bg.width()
        if bg_width > 0:
            self._timer_progress_fill.setFixedWidth(int(bg_width * progress))

    def _import_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入音效", "",
            "Audio (*.mp3 *.wav *.ogg *.m4a);;All Files (*)"
        )
        if not path:
            return
        if path not in self._imported_sounds:
            self._imported_sounds.append(path)
        self._update_sound_list_label()

    def _update_sound_list_label(self):
        if self._imported_sounds:
            names = [Path(p).name for p in self._imported_sounds]
            self._sound_list_label.setText("已导入: " + ", ".join(names))
        else:
            self._sound_list_label.setText("已导入: 无")
