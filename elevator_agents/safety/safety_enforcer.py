from dataclasses import replace
from state.elevator_state import ElevatorCommand, StateSnapshot


class SafetyEnforcer:
    """Pure Python hardware interlocks — runs on every ADS write, no LLM involved."""

    def enforce(self, cmd: ElevatorCommand, state: StateSnapshot) -> ElevatorCommand:
        motor_up = cmd.motor_up
        motor_down = cmd.motor_down
        door_close = cmd.door_close

        # Motor must not run if door is not confirmed closed
        if not state.door_closed:
            motor_up = False
            motor_down = False

        # Both directions simultaneously is forbidden
        if motor_up and motor_down:
            motor_up = False
            motor_down = False

        # Emergency stop overrides everything
        if state.emergency_active:
            motor_up = False
            motor_down = False
            door_close = False

        return ElevatorCommand(
            motor_up=motor_up,
            motor_down=motor_down,
            door_close=door_close,
            lamp_floor=list(cmd.lamp_floor),
            lamp_inside=list(cmd.lamp_inside),
            display=cmd.display,
        )
