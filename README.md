# Elevator Control: TwinCAT PLC + Python Control Layer

A three-floor elevator controlled from Python over the Beckhoff **ADS** protocol, running against a
TwinCAT 3 simulation written in Structured Text. A small neural network makes the door and indicator
decisions; motor direction stays a deterministic latch, and every command passes through a safety
enforcer before it is written to the PLC.


## Why it is built this way

The interesting question in industrial AI is not whether a model *can* drive an actuator, but which
decisions you are willing to hand over. Here the split is explicit:

| Layer | Decides | Implementation |
|---|---|---|
| Motor direction | up / down / stop | Deterministic SR latch in `main.py`, derived from the request queue, floor sensors and door state |
| Doors and indicator lamps | close / open, which lamps are lit | `TinyController` — a ~10,000-parameter MLP (13 inputs → 90 → 90 → 7 outputs), NumPy-only inference |
| Safety | veto | `SafetyEnforcer` — pure Python interlocks applied to **every** command before it reaches the PLC |

The safety enforcer is not advisory. It runs on every ADS write:

- the motor cannot run unless the door is confirmed closed
- both directions at once is impossible
- emergency stop overrides everything

If the network produces a command that violates an interlock, the enforcer rewrites it. The learned
component is therefore confined to the decisions where a wrong answer is an inconvenience, not a hazard.

## Architecture

```
TwinCAT 3 (Structured Text, PLCSim)
        │  GVL variables
        │  ADS protocol, polled every 50 ms
        ▼
ConnectionManager ──► StateMachine ──► StateSnapshot
                            │
                            ▼
                     ElevatorOrchestrator
                     ├── FLOOR_ARRIVED      → queue cleanup, open door
                     ├── BUTTON_PRESSED     → TinyController inference
                     └── DOOR_FULLY_OPEN    → TinyController inference
                            │
                            ▼
                     CommandBuffer ──► SafetyEnforcer ──► ADS write
```

## Repository layout

```
TwinCAT Project Elevator/     TwinCAT 3 solution
  PLCSim/                     elevator simulation and visualisation (Structured Text)
  PLCStudent/                 control program

elevator_agents/
  ads/                        pyads connection, variable map, read/write interface
  state/                      state machine, immutable snapshots, command buffer
  agents/                     orchestrator, TinyController, training script, tools
  safety/                     safety enforcer (hardware interlocks)
  main.py                     event loop, motor latch, ADS polling
  config.py                   ADS net id, port, timings
```

## Running it

Requires TwinCAT 3 with the simulation project loaded and running.

```bash
cd elevator_agents
pip install -r requirements.txt
cp .env.example .env          # set ADS_NET_ID and ADS_PORT for your runtime
python agents/train_model.py  # trains elevator_net.npz (not committed)
python main.py
```

`test_ads.py` verifies the ADS connection and the variable map before you run the full loop.

## Notes

The TwinCAT project skeleton and the elevator simulation were provided as course material. The Python
control layer, the neural controller, the state machine and the safety enforcer under `elevator_agents/`
are my own work.
