from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ElevatorState(Enum):
    IDLE_DOOR_OPEN = auto()
    IDLE_DOOR_CLOSED = auto()
    MOVING_UP = auto()
    MOVING_DOWN = auto()
    DOOR_OPENING = auto()
    DOOR_CLOSING = auto()
    EMERGENCY_STOP = auto()


@dataclass
class StateSnapshot:
    state: ElevatorState = ElevatorState.IDLE_DOOR_OPEN
    current_floor: int = 1          # 1, 2, or 3 (0 = between floors)
    door_open: bool = False
    door_closed: bool = False
    motor_up: bool = False
    motor_down: bool = False
    btn_floor: tuple[bool, bool, bool] = (False, False, False)
    btn_inside: tuple[bool, bool, bool] = (False, False, False)
    btn_green: bool = False
    emergency_active: bool = False  # True when ixButtRed == BUTT_RED_ACTIVE_STATE
    sensor_at_floor: tuple[bool, bool, bool] = (False, False, False)
    request_queue: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "state": self.state.name,
            "current_floor": self.current_floor,
            "door_open": self.door_open,
            "door_closed": self.door_closed,
            "motor_up": self.motor_up,
            "motor_down": self.motor_down,
            "btn_floor": list(self.btn_floor),
            "btn_inside": list(self.btn_inside),
            "btn_green": self.btn_green,
            "emergency_active": self.emergency_active,
            "sensor_at_floor": list(self.sensor_at_floor),
            "request_queue": self.request_queue,
        }


@dataclass
class ElevatorEvent:
    event_type: str   # BUTTON_PRESSED, FLOOR_ARRIVED, DOOR_FULLY_OPEN, DOOR_FULLY_CLOSED, EMERGENCY, QUEUE_EMPTY
    payload: dict
    snapshot: StateSnapshot


@dataclass
class ElevatorCommand:
    motor_up: bool = False
    motor_down: bool = False
    door_close: bool = False
    lamp_floor: list[bool] = field(default_factory=lambda: [False, False, False])
    lamp_inside: list[bool] = field(default_factory=lambda: [False, False, False])
    display: int = 0
