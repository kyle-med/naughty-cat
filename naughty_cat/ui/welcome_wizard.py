from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QCheckBox,
    QSlider, QHBoxLayout, QFormLayout, QWidget
)
from PySide6.QtCore import Qt
from naughty_cat.ui.cat_config import CatConfigPanel


class WelcomeWizard(QWizard):
    def __init__(self, cats=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用 Naughty Cat")
        self.setWizardStyle(QWizard.ModernStyle)

        if cats is None:
            cats = [
                {"name": "大橘", "file": "orange_cat.gif", "builtin": True},
                {"name": "蓝猫", "file": "blue_cat.gif", "builtin": True},
                {"name": "三花", "file": "calico_cat.gif", "builtin": True},
            ]

        self._cat_page = _CatPage(cats)
        self._timer_page = _TimerPage()
        self._done_page = _DonePage()

        self.addPage(self._cat_page)
        self.addPage(self._timer_page)
        self.addPage(self._done_page)

    def get_settings(self) -> dict:
        return {
            "active_cats": self._cat_page.panel.get_active_cats(),
            "cat_count": self._cat_page.panel.get_cat_count(),
            "cat_size": self._cat_page.panel.get_cat_size(),
            "work_interval_min": self._timer_page.work_slider.value(),
            "break_duration_min": self._timer_page.break_slider.value(),
            "idle_threshold_sec": self._timer_page.idle_slider.value(),
            "dismiss_hide_min": self._timer_page.dismiss_slider.value(),
            "auto_start": self._done_page.auto_start_cb.isChecked(),
            "first_run": False,
        }


class _CatPage(QWizardPage):
    def __init__(self, cats, parent=None):
        super().__init__(parent)
        self.setTitle("选择你的猫咪伙伴")
        self.setSubTitle("选择你喜欢的猫咪来提醒你休息")
        layout = QVBoxLayout(self)
        self.panel = CatConfigPanel(
            cats, [c["name"] for c in cats], count=2, size=100
        )
        layout.addWidget(self.panel)


class _TimerPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("设置提醒时间")
        self.setSubTitle("调整工作和休息的时间")
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.work_slider = self._make_slider(15, 120, 50, "分钟")
        self.break_slider = self._make_slider(1, 30, 5, "分钟")
        self.idle_slider = self._make_slider(2, 30, 5, "秒")
        self.dismiss_slider = self._make_slider(1, 30, 1, "分钟")

        form.addRow("工作间隔", self.work_slider)
        form.addRow("休息时长", self.break_slider)
        form.addRow("空闲检测", self.idle_slider)
        form.addRow("驱赶隐藏", self.dismiss_slider)

        layout.addLayout(form)

    def _make_slider(self, lo, hi, default, unit):
        w = QWidget(self)
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(default)
        label = QLabel(f"{default} {unit}")
        slider.valueChanged.connect(lambda v, l=label, u=unit: l.setText(f"{v} {u}"))
        layout.addWidget(slider)
        layout.addWidget(label)
        return slider


class _DonePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("准备就绪！")
        self.setSubTitle("Naughty Cat 已经配置好了")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("你的猫咪会在工作时间结束后出来提醒你休息。"))
        layout.addWidget(QLabel("记得让你的猫咪来照顾你的健康！"))
        self.auto_start_cb = QCheckBox("开机自动启动")
        self.auto_start_cb.setChecked(True)
        layout.addWidget(self.auto_start_cb)
