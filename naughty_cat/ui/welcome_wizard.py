from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QCheckBox,
    QFormLayout
)
from PySide6.QtCore import Qt
from naughty_cat.ui.cat_config import CatConfigPanel
from naughty_cat.ui.style import make_slider_row


class WelcomeWizard(QWizard):
    def __init__(self, cats=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用 Naughty Cat")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(440, 480)

        if cats is None:
            cats = [
                {"name": "波仔", "file": "波仔.gif", "builtin": True},
                {"name": "咣当", "file": "咣当.gif", "builtin": True},
                {"name": "Bender", "file": "Bender.gif", "builtin": True},
                {"name": "胖虎（不过已经去喵星了TuT）", "file": "胖虎.gif", "builtin": True},
            ]

        self._intro_page = _WelcomePage()
        self._cat_page = _CatPage(cats)
        self._timer_page = _TimerPage()
        self._done_page = _DonePage()

        self.addPage(self._intro_page)
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


class _WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("欢迎来到 Naughty Cat \U0001F431")
        self.setSubTitle("一个用猫咪提醒你休息的小工具")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        why = QLabel(
            "\U0001F4A1 设计初衷\n"
            "长时间工作会损害你的身体和注意力。"
            "Naughty Cat 帮你定时休息，"
            "让可爱的小猫咪来提醒你该走动一下了。"
        )
        why.setWordWrap(True)
        why.setStyleSheet("font-size: 14px; color: #1C1C1E; line-height: 1.6;")
        layout.addWidget(why)

        where = QLabel(
            "\U0001F4CD 软件位置\n"
            "打开后，Naughty Cat 会安静地待在"
            "你屏幕右下角的系统托盘（仪表盘）里。"
            "右键点击猫咪图标就能打开菜单，"
            "调整设置或暂停提醒。"
        )
        where.setWordWrap(True)
        where.setStyleSheet("font-size: 14px; color: #1C1C1E; line-height: 1.6;")
        layout.addWidget(where)

        how = QLabel(
            "\U0001F3AE 主要用法\n"
            "① 工作设定时长后，猫咪会在屏幕上游走\n"
            "② 点击猫咪可以临时驱赶，但它们一会儿还会回来\n"
            "③ 只有真正停下手头休息足够时间，猫咪才会离开\n"
            "④ 休息结束后会自动开始下一轮工作计时"
        )
        how.setWordWrap(True)
        how.setStyleSheet("font-size: 14px; color: #1C1C1E; line-height: 1.6;")
        layout.addWidget(how)

        layout.addStretch()


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

        self.work_slider, work_row = make_slider_row(3, 120, 50, "分钟")
        self.break_slider, break_row = make_slider_row(1, 30, 5, "分钟")
        self.idle_slider, idle_row = make_slider_row(2, 30, 5, "秒")
        self.dismiss_slider, dismiss_row = make_slider_row(1, 30, 1, "分钟")

        form.addRow("工作间隔", work_row)
        form.addRow("休息时长", break_row)
        form.addRow("空闲检测", idle_row)
        form.addRow("驱赶隐藏", dismiss_row)

        layout.addLayout(form)


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
