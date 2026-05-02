from enum import Enum, auto
from PySide6.QtCore import QObject, QTimer, Signal


class State(Enum):
    WORKING = auto()
    CAT_SHOW = auto()
    RESTING = auto()
    RESTING_PAUSED = auto()
    CAT_HIDING = auto()
    REST_DONE = auto()


class Event(Enum):
    WORK_TIMER_FIRE = auto()
    IDLE_DETECTED = auto()
    USER_ACTIVE = auto()
    BREAK_COMPLETE = auto()
    DISMISS_CLICKED = auto()
    HIDE_TIMER_FIRE = auto()
    USER_ACKNOWLEDGE = auto()
    MANUAL_SUMMON = auto()


class StateMachine(QObject):
    state_changed = Signal(State)
    paused_changed = Signal(bool)

    def __init__(self, work_interval_min, break_duration_min,
                 idle_threshold_sec, dismiss_hide_min, parent=None):
        super().__init__(parent)
        self._work_interval_ms = int(work_interval_min * 60 * 1000)
        self._break_duration_ms = int(break_duration_min * 60 * 1000)
        self._dismiss_hide_ms = int(dismiss_hide_min * 60 * 1000)
        self._idle_threshold = idle_threshold_sec

        self._current_state = State.WORKING
        self.is_paused = False
        self._break_remaining_ms = None  # saved break progress across dismiss

        self._work_timer = QTimer(self)
        self._work_timer.setSingleShot(True)
        self._work_timer.timeout.connect(self._on_work_timer_fire)

        self._break_timer = QTimer(self)
        self._break_timer.setSingleShot(True)
        self._break_timer.timeout.connect(self._on_break_timer_fire)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide_timer_fire)

    @property
    def current_state(self) -> State:
        return self._current_state

    def start(self):
        self._start_work_timer()

    def transition(self, event: Event):
        state = self._current_state

        if event == Event.WORK_TIMER_FIRE and state == State.WORKING:
            self._set_state(State.CAT_SHOW)

        elif event == Event.IDLE_DETECTED:
            if state == State.CAT_SHOW:
                self._set_state(State.RESTING)
                self._start_break_timer()
            elif state == State.RESTING_PAUSED:
                self._set_state(State.RESTING)
                self._start_break_timer()

        elif event == Event.USER_ACTIVE:
            if state == State.RESTING:
                self._break_remaining_ms = self._break_timer.remainingTime()
                self._break_timer.stop()
                self._set_state(State.RESTING_PAUSED)

        elif event == Event.DISMISS_CLICKED:
            if state == State.RESTING:
                self._break_remaining_ms = self._break_timer.remainingTime()
                self._break_timer.stop()
            elif state == State.RESTING_PAUSED:
                # Remaining time already saved in USER_ACTIVE
                pass
            elif state == State.CAT_SHOW:
                pass
            if state in (State.CAT_SHOW, State.RESTING, State.RESTING_PAUSED):
                self._break_timer.stop()
                self._set_state(State.CAT_HIDING)
                self._start_hide_timer()

        elif event == Event.HIDE_TIMER_FIRE and state == State.CAT_HIDING:
            self._set_state(State.CAT_SHOW)

        elif event == Event.BREAK_COMPLETE and state == State.RESTING:
            self._break_remaining_ms = None
            self._set_state(State.REST_DONE)

        elif event == Event.USER_ACKNOWLEDGE and state == State.REST_DONE:
            self._break_remaining_ms = None
            self._set_state(State.WORKING)
            self._start_work_timer()

        elif event == Event.MANUAL_SUMMON:
            self._work_timer.stop()
            self._break_timer.stop()
            self._hide_timer.stop()
            self._break_remaining_ms = None
            self._set_state(State.CAT_SHOW)

    def pause(self):
        self.is_paused = True
        self._work_timer.stop()
        self.paused_changed.emit(True)

    def resume(self):
        self.is_paused = False
        self._start_work_timer()
        self.paused_changed.emit(False)

    def update_intervals(self, work_interval_min, break_duration_min,
                         dismiss_hide_min):
        old_work_ms = self._work_interval_ms
        self._work_interval_ms = int(work_interval_min * 60 * 1000)
        self._break_duration_ms = int(break_duration_min * 60 * 1000)
        self._dismiss_hide_ms = int(dismiss_hide_min * 60 * 1000)

        if self._current_state == State.WORKING and self._work_timer.isActive():
            remaining = self._work_timer.remainingTime()
            elapsed = old_work_ms - remaining
            new_remaining = max(0, self._work_interval_ms - elapsed)
            self._work_timer.start(new_remaining)

    def timer_info(self) -> dict:
        info = {
            "state": self._current_state,
            "remaining_ms": None,
            "total_ms": None,
        }
        if self._current_state == State.WORKING and self._work_timer.isActive():
            info["remaining_ms"] = self._work_timer.remainingTime()
            info["total_ms"] = self._work_interval_ms
        elif self._current_state == State.RESTING and self._break_timer.isActive():
            info["remaining_ms"] = self._break_timer.remainingTime()
            info["total_ms"] = self._break_duration_ms
        elif self._current_state == State.RESTING_PAUSED:
            info["remaining_ms"] = self._break_remaining_ms or self._break_duration_ms
            info["total_ms"] = self._break_duration_ms
        elif self._current_state == State.CAT_HIDING and self._hide_timer.isActive():
            info["remaining_ms"] = self._hide_timer.remainingTime()
            info["total_ms"] = self._dismiss_hide_ms
        return info

    # --- internal ---

    def _force_state(self, state: State):
        """Test helper: jump to a state without timers."""
        self._work_timer.stop()
        self._break_timer.stop()
        self._hide_timer.stop()
        self._current_state = state

    def _set_state(self, state: State):
        self._current_state = state
        self.state_changed.emit(state)

    def _start_work_timer(self):
        if not self.is_paused:
            self._work_timer.start(self._work_interval_ms)

    def _start_break_timer(self):
        duration = self._break_remaining_ms or self._break_duration_ms
        self._break_remaining_ms = None
        self._break_timer.start(duration)

    def _start_hide_timer(self):
        self._hide_timer.start(self._dismiss_hide_ms)

    def _on_work_timer_fire(self):
        self.transition(Event.WORK_TIMER_FIRE)

    def _on_break_timer_fire(self):
        self.transition(Event.BREAK_COMPLETE)

    def _on_hide_timer_fire(self):
        self.transition(Event.HIDE_TIMER_FIRE)
