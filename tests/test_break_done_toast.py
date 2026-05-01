from PySide6.QtCore import QCoreApplication, Qt
from naughty_cat.ui.break_done_toast import BreakDoneToast


def test_toast_shows_and_emits_on_click(qtbot):
    toast = BreakDoneToast()
    qtbot.addWidget(toast)
    toast.show()
    assert toast.isVisible()

    acknowledged = False

    def on_ack():
        nonlocal acknowledged
        acknowledged = True

    toast.acknowledged.connect(on_ack)
    toast._btn.click()
    assert acknowledged is True


def test_toast_auto_dismisses(qtbot):
    toast = BreakDoneToast(auto_dismiss_ms=50)
    qtbot.addWidget(toast)
    toast.show()

    acknowledged = False

    def on_ack():
        nonlocal acknowledged
        acknowledged = True

    toast.acknowledged.connect(on_ack)

    qtbot.waitUntil(lambda: acknowledged, timeout=2000)
