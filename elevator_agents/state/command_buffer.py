import threading
from state.elevator_state import ElevatorCommand


class CommandBuffer:
    """Thread-safe bridge between agent decisions and the ADS I/O loop."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cmd = ElevatorCommand()

    def set_command(self, cmd: ElevatorCommand):
        with self._lock:
            self._cmd = cmd

    def get_command(self) -> ElevatorCommand:
        with self._lock:
            return ElevatorCommand(
                motor_up=self._cmd.motor_up,
                motor_down=self._cmd.motor_down,
                door_close=self._cmd.door_close,
                lamp_floor=list(self._cmd.lamp_floor),
                lamp_inside=list(self._cmd.lamp_inside),
                display=self._cmd.display,
            )
