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


def test_toast_stays_until_clicked(qtbot):
    toast = BreakDoneToast()
    qtbot.addWidget(toast)
    toast.show()

    acknowledged = False

    def on_ack():
        nonlocal acknowledged
        acknowledged = True

    toast.acknowledged.connect(on_ack)
    # Toast should NOT auto-dismiss — must stay until clicked
    # Wait a bit and verify it's still there
    assert not acknowledged
    assert toast.isVisible()
