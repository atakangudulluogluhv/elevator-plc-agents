import asyncio
import logging
from state.elevator_state import ElevatorEvent
from state.state_machine import StateMachine
from state.command_buffer import CommandBuffer
from safety.safety_enforcer import SafetyEnforcer
from agents.tools import elevator_tools as tools
from agents.tiny_controller import TinyController

log = logging.getLogger(__name__)


class ElevatorOrchestrator:
    def __init__(self, sm: StateMachine, buf: CommandBuffer, enforcer: SafetyEnforcer):
        self._sm = sm
        self._buf = buf
        self._enforcer = enforcer
        self._semaphore = asyncio.Semaphore(1)

        tools.init_tools(sm, buf, enforcer)
        self._ctrl = TinyController()
        log.info("TinyController loaded (%.0fK params)", 10.087)

    def _handle_floor_arrived(self, floor: int):
        """Queue cleanup and door open on arrival — motor stop handled by ads_loop latch."""
        state = self._sm.get_snapshot()
        if floor in state.request_queue:
            self._sm.remove_from_queue(floor)
            tools._pending.door_close = False
            remaining = self._sm.get_snapshot().request_queue
            tools._pending.lamp_floor = [i + 1 in remaining for i in range(3)]
            tools._pending.lamp_inside = [i + 1 in remaining for i in range(3)]
        tools._pending.display = floor
        result = tools.commit_command()
        log.info("FLOOR_ARRIVED at floor %s: %s", floor, result)

    def _handle_with_model(self, event_type: str, state, payload: dict):
        """Run tiny MLP inference and commit result to CommandBuffer."""
        decision = self._ctrl.predict(event_type, state, payload)
        tools._pending.door_close = decision["door_close"]
        tools._pending.lamp_floor = list(decision["lamp_floor"])
        tools._pending.lamp_inside = list(decision["lamp_inside"])
        tools._pending.display = state.current_floor
        result = tools.commit_command()
        log.info("%s -> door_close=%s lamps=%s | %s",
                 event_type, decision["door_close"], decision["lamp_floor"], result)

    async def handle_event(self, event: ElevatorEvent):
        async with self._semaphore:
            state = self._sm.get_snapshot()
            log.info("Handling event: %s %s", event.event_type, event.payload)

            if event.event_type == "FLOOR_ARRIVED":
                self._handle_floor_arrived(event.payload.get("floor", 0))
                return

            if event.event_type in ("DOOR_FULLY_CLOSED", "EMERGENCY", "QUEUE_EMPTY"):
                return  # Motor latch and SafetyEnforcer handle these

            if event.event_type in ("BUTTON_PRESSED", "DOOR_FULLY_OPEN"):
                self._handle_with_model(event.event_type, state, event.payload)
                return
