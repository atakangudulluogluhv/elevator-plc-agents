import asyncio
import logging
import sys
from dataclasses import replace
from ads.connection_manager import ConnectionManager
from ads.variable_map import BOOL_OUTPUTS, OUT_LAMP_LEVEL, OUT_MOTOR_UP, OUT_MOTOR_DOWN, OUT_LAMP_INSIDE, OUT_DOOR_CLOSE
from state.elevator_state import ElevatorCommand, StateSnapshot
from state.state_machine import StateMachine
from state.command_buffer import CommandBuffer
from safety.safety_enforcer import SafetyEnforcer
from agents.orchestrator import ElevatorOrchestrator
from config import ADS_NET_ID, ADS_PORT, ADS_POLL_INTERVAL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("main")


_prev_motor: tuple[bool, bool] = (False, False)


def _compute_motor(state: StateSnapshot) -> tuple[bool, bool]:
    """SR latch: motor direction from queue + door + sensor, updated every 50ms."""
    global _prev_motor
    if not state.request_queue or not state.door_closed:
        result = (False, False)
    else:
        target = state.request_queue[0]
        if state.sensor_at_floor[target - 1]:
            result = (False, False)
        elif target > state.current_floor:
            result = (True, False)
        elif target < state.current_floor:
            result = (False, True)
        else:
            result = (False, False)

    if result != _prev_motor:
        log.info("Motor latch: up=%s down=%s | floor=%s queue=%s door_closed=%s",
                 result[0], result[1], state.current_floor,
                 state.request_queue, state.door_closed)
        _prev_motor = result
    return result


def _build_output_bools(cmd: ElevatorCommand) -> dict[str, bool]:
    bools = {}
    for i, sym in enumerate(OUT_LAMP_LEVEL):
        bools[sym] = cmd.lamp_floor[i]
    bools[OUT_MOTOR_UP] = cmd.motor_up
    bools[OUT_MOTOR_DOWN] = cmd.motor_down
    for i, sym in enumerate(OUT_LAMP_INSIDE):
        bools[sym] = cmd.lamp_inside[i]
    bools[OUT_DOOR_CLOSE] = cmd.door_close
    return bools


async def ads_loop(conn: ConnectionManager, sm: StateMachine, buf: CommandBuffer, enforcer: SafetyEnforcer):
    log.info("ADS I/O loop starting (%.0fms cycle)", ADS_POLL_INTERVAL * 1000)
    while True:
        raw = await conn.read_inputs()
        if raw is not None:
            sm.process(raw)                                    # uses prev motor state for FLOOR_ARRIVED detection
            state = sm.get_snapshot()
            motor_up, motor_down = _compute_motor(state)      # SR latch
            sm.set_motor_state(motor_up, motor_down)          # update for next cycle's event detection
            cmd = buf.get_command()
            cmd = replace(cmd, motor_up=motor_up, motor_down=motor_down)
            safe_cmd = enforcer.enforce(cmd, state)
            bools = _build_output_bools(safe_cmd)
            await conn.write_outputs(bools, safe_cmd.display)
        await asyncio.sleep(ADS_POLL_INTERVAL)


async def agent_loop(event_queue: asyncio.Queue, orchestrator: ElevatorOrchestrator):
    log.info("Agent loop started")
    while True:
        event = await event_queue.get()
        asyncio.create_task(orchestrator.handle_event(event))


async def main():
    event_queue: asyncio.Queue = asyncio.Queue(maxsize=10)

    conn = ConnectionManager(ADS_NET_ID, ADS_PORT)
    sm = StateMachine(event_queue)
    buf = CommandBuffer()
    enforcer = SafetyEnforcer()
    orchestrator = ElevatorOrchestrator(sm, buf, enforcer)

    log.info("Connecting to TwinCAT ADS %s:%d ...", ADS_NET_ID, ADS_PORT)
    await conn.ensure_connected()

    await asyncio.gather(
        ads_loop(conn, sm, buf, enforcer),
        agent_loop(event_queue, orchestrator),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Stopped by user")
