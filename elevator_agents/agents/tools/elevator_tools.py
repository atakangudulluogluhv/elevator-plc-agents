"""
Shared mutable state used by agent tools.
Initialized in orchestrator.py before agents run.
"""
from state.elevator_state import ElevatorCommand, StateSnapshot
from state.command_buffer import CommandBuffer
from state.state_machine import StateMachine
from safety.safety_enforcer import SafetyEnforcer

# These are set by the orchestrator before agent tools are called
_state_machine: StateMachine | None = None
_command_buffer: CommandBuffer | None = None
_safety_enforcer: SafetyEnforcer | None = None
_pending: ElevatorCommand = ElevatorCommand()


def init_tools(sm: StateMachine, buf: CommandBuffer, enforcer: SafetyEnforcer):
    global _state_machine, _command_buffer, _safety_enforcer, _pending
    _state_machine = sm
    _command_buffer = buf
    _safety_enforcer = enforcer
    _pending = ElevatorCommand()


def _reset_pending():
    global _pending
    prev = _command_buffer.get_command()
    _pending = ElevatorCommand(
        motor_up=prev.motor_up,
        motor_down=prev.motor_down,
        door_close=prev.door_close,
        lamp_floor=list(prev.lamp_floor),
        lamp_inside=list(prev.lamp_inside),
        display=prev.display,
    )


def get_current_state() -> dict:
    """Returns the current elevator state snapshot."""
    return _state_machine.get_snapshot().to_dict()


def set_motor_command(command: str) -> str:
    """Set motor command. command must be 'up', 'down', or 'stop'."""
    global _pending
    command = command.lower().strip()
    if command == "up":
        _pending.motor_up = True
        _pending.motor_down = False
    elif command == "down":
        _pending.motor_up = False
        _pending.motor_down = True
    elif command == "stop":
        _pending.motor_up = False
        _pending.motor_down = False
    else:
        return f"Unknown command '{command}'. Use 'up', 'down', or 'stop'."
    return f"Motor set to {command}"


def _to_bool(v) -> bool:
    """Convert string 'True'/'False' or bool to actual bool."""
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def set_door_close(close: bool) -> str:
    """True = command door to close and stay closed. False = allow door to open."""
    global _pending
    _pending.door_close = _to_bool(close)
    return f"Door close command = {_pending.door_close}"


def set_floor_lamps(floor1: bool, floor2: bool, floor3: bool) -> str:
    """Set the call button lamps at each floor landing."""
    global _pending
    _pending.lamp_floor = [_to_bool(floor1), _to_bool(floor2), _to_bool(floor3)]
    return f"Floor lamps = {_pending.lamp_floor}"


def set_cabin_lamps(floor1: bool, floor2: bool, floor3: bool) -> str:
    """Set the destination button lamps inside the elevator cabin."""
    global _pending
    _pending.lamp_inside = [_to_bool(floor1), _to_bool(floor2), _to_bool(floor3)]
    return f"Cabin lamps = {_pending.lamp_inside}"


def set_display(floor_number: int) -> str:
    """Set the floor number shown on the display inside the elevator (1, 2, or 3)."""
    global _pending
    _pending.display = int(floor_number)
    return f"Display = {floor_number}"


def add_floor_to_queue(floor: int) -> str:
    """Add a floor to the pending service queue if not already present."""
    _state_machine.add_to_queue(int(floor))
    return f"Floor {floor} added to queue. Queue = {_state_machine.get_snapshot().request_queue}"


def remove_floor_from_queue(floor: int) -> str:
    """Remove a floor from the service queue (floor was served)."""
    _state_machine.remove_from_queue(int(floor))
    return f"Floor {floor} removed. Queue = {_state_machine.get_snapshot().request_queue}"


def commit_command() -> str:
    """
    SafetyMonitorAgent calls this after validating the proposed command.
    Applies safety interlocks and writes to the CommandBuffer.
    Returns 'COMMAND_COMMITTED' on success.
    """
    state = _state_machine.get_snapshot()
    safe_cmd = _safety_enforcer.enforce(_pending, state)
    _command_buffer.set_command(safe_cmd)
    _reset_pending()
    return "COMMAND_COMMITTED"
