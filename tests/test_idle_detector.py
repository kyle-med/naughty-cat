import time
from PySide6.QtCore import QCoreApplication
from naughty_cat.idle_detector import IdleDetector


def test_idle_detector_starts_and_emits(qtbot):
    app = QCoreApplication.instance() or QCoreApplication([])
    detector = IdleDetector(check_interval_ms=100, idle_threshold_sec=0.05)
    signals_received = []

    def on_idle_changed(seconds):
        signals_received.append(seconds)

    detector.idle_seconds_changed.connect(on_idle_changed)
    detector.start()

    def check():
        assert len(signals_received) > 0
        assert signals_received[-1] >= 0  # idle seconds is a non-negative number

    qtbot.waitUntil(check, timeout=2000)


def test_idle_detector_stops(qtbot):
    detector = IdleDetector(check_interval_ms=50, idle_threshold_sec=60)
    detector.start()
    detector.stop()
    # After stop, no more signals should fire
    count_before = 0

    def on_idle_changed(seconds):
        nonlocal count_before
        count_before += 1

    detector.idle_seconds_changed.connect(on_idle_changed)

    def assert_stable():
        cnt = count_before
        time.sleep(0.3)
        assert cnt == count_before  # no new signals

    qtbot.waitUntil(assert_stable, timeout=2000)


def test_idle_detector_emits_became_idle(qtbot):
    app = QCoreApplication.instance() or QCoreApplication([])
    detector = IdleDetector(check_interval_ms=50, idle_threshold_sec=0.05)
    became_idle_called = False

    def on_became_idle():
        nonlocal became_idle_called
        became_idle_called = True

    detector.became_idle.connect(on_became_idle)
    detector.start()

    qtbot.waitUntil(lambda: became_idle_called, timeout=3000)


def test_update_threshold():
    detector = IdleDetector(idle_threshold_sec=5)
    assert detector._idle_threshold == 5
    detector.update_threshold(10)
    assert detector._idle_threshold == 10
