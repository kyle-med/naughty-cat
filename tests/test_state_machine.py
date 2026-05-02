from PySide6.QtCore import QCoreApplication, QTimer
from naughty_cat.state_machine import StateMachine, State, Event


def test_initial_state_is_working():
    app = QCoreApplication.instance() or QCoreApplication([])
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    assert sm.current_state == State.WORKING


def test_work_timer_fire_transitions_to_cat_show(qtbot):
    sm = StateMachine(work_interval_min=0.001, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    cat_show_reached = False

    def on_state_changed(new_state):
        nonlocal cat_show_reached
        if new_state == State.CAT_SHOW:
            cat_show_reached = True

    sm.state_changed.connect(on_state_changed)
    sm.start()

    qtbot.waitUntil(lambda: cat_show_reached, timeout=3000)
    assert sm.current_state == State.CAT_SHOW


def test_idle_detected_transitions_to_resting(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.CAT_SHOW)
    resting_reached = False

    def on_state_changed(new_state):
        nonlocal resting_reached
        if new_state == State.RESTING:
            resting_reached = True

    sm.state_changed.connect(on_state_changed)
    sm.transition(Event.IDLE_DETECTED)

    qtbot.waitUntil(lambda: resting_reached, timeout=500)
    assert sm.current_state == State.RESTING


def test_user_active_pauses_resting(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING)
    sm.transition(Event.USER_ACTIVE)
    qtbot.waitUntil(lambda: sm.current_state == State.RESTING_PAUSED, timeout=500)


def test_idle_resumes_from_paused(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING_PAUSED)
    sm.transition(Event.IDLE_DETECTED)
    qtbot.waitUntil(lambda: sm.current_state == State.RESTING, timeout=500)


def test_dismiss_transitions_to_hiding(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=0.001)
    sm._force_state(State.CAT_SHOW)
    hiding_reached = False

    def on_state_changed(new_state):
        nonlocal hiding_reached
        if new_state == State.CAT_HIDING:
            hiding_reached = True

    sm.state_changed.connect(on_state_changed)
    sm.transition(Event.DISMISS_CLICKED)

    qtbot.waitUntil(lambda: hiding_reached, timeout=3000)


def test_hide_timer_fire_returns_to_cat_show(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=0.001)
    sm._force_state(State.CAT_HIDING)
    sm._start_hide_timer()
    cat_show_reached = False

    def on_state_changed(new_state):
        nonlocal cat_show_reached
        if new_state == State.CAT_SHOW:
            cat_show_reached = True

    sm.state_changed.connect(on_state_changed)

    qtbot.waitUntil(lambda: cat_show_reached, timeout=3000)


def test_break_complete_transitions_to_rest_done(qtbot):
    sm = StateMachine(work_interval_min=60, break_duration_min=0.001,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING)
    sm._start_break_timer()
    rest_done_reached = False

    def on_state_changed(new_state):
        nonlocal rest_done_reached
        if new_state == State.REST_DONE:
            rest_done_reached = True

    sm.state_changed.connect(on_state_changed)

    qtbot.waitUntil(lambda: rest_done_reached, timeout=3000)


def test_user_acknowledge_resets_to_working(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.REST_DONE)
    sm.transition(Event.USER_ACKNOWLEDGE)
    qtbot.waitUntil(lambda: sm.current_state == State.WORKING, timeout=500)


def test_manual_summon_from_working(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm.transition(Event.MANUAL_SUMMON)
    qtbot.waitUntil(lambda: sm.current_state == State.CAT_SHOW, timeout=500)


def test_manual_summon_from_hiding(qtbot):
    """Bug fix: manual summon should work even after dismissing cats."""
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.CAT_HIDING)
    sm.transition(Event.MANUAL_SUMMON)
    qtbot.waitUntil(lambda: sm.current_state == State.CAT_SHOW, timeout=500)


def test_manual_summon_from_rest_done(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.REST_DONE)
    sm.transition(Event.MANUAL_SUMMON)
    qtbot.waitUntil(lambda: sm.current_state == State.CAT_SHOW, timeout=500)


def test_pause_and_resume(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm.pause()
    assert sm.is_paused is True
    sm.resume()
    assert sm.is_paused is False
    assert sm.current_state == State.WORKING


def test_update_intervals_updates_stored_values():
    app = QCoreApplication.instance() or QCoreApplication([])
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm.update_intervals(work_interval_min=30, break_duration_min=10,
                        dismiss_hide_min=3)
    assert sm._work_interval_ms == 30 * 60 * 1000
    assert sm._break_duration_ms == 10 * 60 * 1000
    assert sm._dismiss_hide_ms == 3 * 60 * 1000


def test_update_intervals_while_working_preserves_elapsed(qtbot):
    sm = StateMachine(work_interval_min=0.001, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.WORKING)
    sm._start_work_timer()
    assert sm._work_timer.isActive()
    remaining_before = sm._work_timer.remainingTime()
    # Change to 60 min — remaining should jump way up (most of 60 min left)
    sm.update_intervals(work_interval_min=60, break_duration_min=5,
                        dismiss_hide_min=1)
    remaining_after = sm._work_timer.remainingTime()
    assert remaining_after > remaining_before
    # Should be close to 60 min (minus the few ms elapsed)
    assert remaining_after > 50 * 60 * 1000


def test_update_intervals_during_resting_does_not_interrupt(qtbot):
    sm = StateMachine(work_interval_min=50, break_duration_min=0.001,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.RESTING)
    sm._start_break_timer()
    remaining_before = sm._break_timer.remainingTime()
    sm.update_intervals(work_interval_min=30, break_duration_min=60,
                        dismiss_hide_min=3)
    # Break timer is NOT interrupted, still running with old short value
    assert sm._break_timer.isActive()
    assert sm._break_timer.remainingTime() < 2000


def test_update_intervals_when_idle_does_not_restart_timer(qtbot):
    """When no timer is active (e.g. CAT_SHOW), update_intervals just stores values."""
    sm = StateMachine(work_interval_min=50, break_duration_min=5,
                      idle_threshold_sec=5, dismiss_hide_min=1)
    sm._force_state(State.CAT_SHOW)
    sm.update_intervals(work_interval_min=30, break_duration_min=10,
                        dismiss_hide_min=3)
    assert sm._work_interval_ms == 30 * 60 * 1000
    assert sm._break_duration_ms == 10 * 60 * 1000
    assert sm._dismiss_hide_ms == 3 * 60 * 1000
