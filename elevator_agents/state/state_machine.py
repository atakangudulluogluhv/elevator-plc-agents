import asyncio
import logging
from ads.variable_map import (
    IN_BTN_LEVEL, IN_SENSOR_LEVEL, IN_BTN_GREEN, IN_BTN_RED,
    IN_BTN_INSIDE, IN_DOOR_CLOSED, IN_DOOR_OPEN,
)
from state.elevator_state import ElevatorState, StateSnapshot, ElevatorEvent
from config import BUTT_RED_ACTIVE_STATE

log = logging.getLogger(__name__)


class StateMachine:
    def __init__(self, event_queue: asyncio.Queue):
        self._q = event_queue
        self._snap = StateSnapshot()
        self._prev_raw: dict = {}
        self._request_queue: list[int] = []
        self._motor_up = False
        self._motor_down = False

    def get_snapshot(self) -> StateSnapshot:
        return self._snap

    def set_motor_state(self, motor_up: bool, motor_down: bool):
        self._motor_up = motor_up
        self._motor_down = motor_down

    def add_to_queue(self, floor: int):
        if floor not in self._request_queue:
            self._request_queue.append(floor)

    def remove_from_queue(self, floor: int):
        if floor in self._request_queue:
            self._request_queue.remove(floor)

    def process(self, raw: dict):
        prev = self._prev_raw

        btn_floor = tuple(raw[IN_BTN_LEVEL[i]] for i in range(3))
        btn_inside = tuple(raw[IN_BTN_INSIDE[i]] for i in range(3))
        sensor = tuple(raw[IN_SENSOR_LEVEL[i]] for i in range(3))
        door_open = raw[IN_DOOR_OPEN]
        door_closed = raw[IN_DOOR_CLOSED]
        btn_red = raw[IN_BTN_RED]
        btn_green = raw[IN_BTN_GREEN]
        emergency = (btn_red == BUTT_RED_ACTIVE_STATE)

        # Determine current floor from sensors
        current_floor = self._snap.current_floor
        for i, s in enumerate(sensor):
            if s:
                current_floor = i + 1

        # Build state
        if emergency:
            state = ElevatorState.EMERGENCY_STOP
        elif self._snap.motor_up:
            state = ElevatorState.MOVING_UP
        elif self._snap.motor_down:
            state = ElevatorState.MOVING_DOWN
        elif door_open:
            state = ElevatorState.IDLE_DOOR_OPEN
        elif door_closed:
            state = ElevatorState.IDLE_DOOR_CLOSED
        else:
            state = ElevatorState.DOOR_CLOSING if self._snap.state in (
                ElevatorState.IDLE_DOOR_OPEN, ElevatorState.DOOR_OPENING
            ) else ElevatorState.DOOR_OPENING

        snap = StateSnapshot(
            state=state,
            current_floor=current_floor,
            door_open=door_open,
            door_closed=door_closed,
            motor_up=self._motor_up,
            motor_down=self._motor_down,
            btn_floor=btn_floor,
            btn_inside=btn_inside,
            btn_green=btn_green,
            emergency_active=emergency,
            sensor_at_floor=sensor,
            request_queue=list(self._request_queue),
        )
        self._snap = snap

        # Detect events (rising/falling edges)
        if prev:
            self._detect_events(raw, prev, snap)

        self._prev_raw = raw

    def _rising(self, sym: str, raw: dict, prev: dict) -> bool:
        return raw.get(sym, False) and not prev.get(sym, False)

    def _falling(self, sym: str, raw: dict, prev: dict) -> bool:
        return not raw.get(sym, True) and prev.get(sym, True)

    def _detect_events(self, raw: dict, prev: dict, snap: StateSnapshot):
        # Floor call buttons
        for i in range(3):
            if self._rising(IN_BTN_LEVEL[i], raw, prev):
                floor = i + 1
                self.add_to_queue(floor)
                self._emit(ElevatorEvent("BUTTON_PRESSED", {"floor": floor, "source": "level"}, snap))

        # Inside cabin buttons
        for i in range(3):
            if self._rising(IN_BTN_INSIDE[i], raw, prev):
                floor = i + 1
                self.add_to_queue(floor)
                self._emit(ElevatorEvent("BUTTON_PRESSED", {"floor": floor, "source": "inside"}, snap))

        # Floor sensor arrival while moving
        if self._motor_up or self._motor_down:
            for i in range(3):
                if self._rising(IN_SENSOR_LEVEL[i], raw, prev):
                    self._emit(ElevatorEvent("FLOOR_ARRIVED", {"floor": i + 1}, snap))

        # Door fully open
        if self._rising(IN_DOOR_OPEN, raw, prev):
            self._emit(ElevatorEvent("DOOR_FULLY_OPEN", {}, snap))

        # Door fully closed
        if self._rising(IN_DOOR_CLOSED, raw, prev):
            self._emit(ElevatorEvent("DOOR_FULLY_CLOSED", {}, snap))

        # Emergency (NC button pressed = falling edge on ixButtRed)
        if self._falling(IN_BTN_RED, raw, prev):
            self._emit(ElevatorEvent("EMERGENCY", {}, snap))

    def _emit(self, event: ElevatorEvent):
        log.info("EVENT: %s %s", event.event_type, event.payload)
        try:
            self._q.put_nowait(event)
        except asyncio.QueueFull:
            log.warning("Event queue full, dropping: %s", event.event_type)
