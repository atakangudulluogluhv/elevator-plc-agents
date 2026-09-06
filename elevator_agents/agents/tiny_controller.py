"""
Tiny MLP elevator controller — ~10K parameters, pure numpy inference.
Architecture: 13 inputs -> 90 -> 90 -> 7 outputs (sigmoid).
Load with TinyController(); call predict(event_type, state, payload).
"""
import numpy as np
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "elevator_net.npz"


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, x)


class ElevatorNet:
    """Pure numpy 3-layer MLP. W shapes: (90,13), (90,90), (7,90)."""

    def __init__(self, weights: dict):
        self.W1 = weights["W1"]
        self.b1 = weights["b1"]
        self.W2 = weights["W2"]
        self.b2 = weights["b2"]
        self.W3 = weights["W3"]
        self.b3 = weights["b3"]

    def forward(self, x: np.ndarray) -> np.ndarray:
        h1 = _relu(self.W1 @ x + self.b1)
        h2 = _relu(self.W2 @ h1 + self.b2)
        return _sigmoid(self.W3 @ h2 + self.b3)

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> "ElevatorNet":
        data = np.load(path)
        return cls(dict(data))


def encode_input(event_type: str, current_floor: int, door_open: bool,
                 door_closed: bool, queue: list[int], payload_floor: int) -> np.ndarray:
    """Encode event + state into the 13-dim input vector."""
    x = np.zeros(13, dtype=np.float32)
    x[0] = 1.0 if event_type == "BUTTON_PRESSED" else 0.0
    x[1] = 1.0 if event_type == "DOOR_FULLY_OPEN" else 0.0
    x[2] = 1.0 if current_floor == 1 else 0.0
    x[3] = 1.0 if current_floor == 2 else 0.0
    x[4] = 1.0 if current_floor == 3 else 0.0
    x[5] = 1.0 if door_open else 0.0
    x[6] = 1.0 if door_closed else 0.0
    x[7] = 1.0 if 1 in queue else 0.0
    x[8] = 1.0 if 2 in queue else 0.0
    x[9] = 1.0 if 3 in queue else 0.0
    x[10] = 1.0 if payload_floor == 1 else 0.0
    x[11] = 1.0 if payload_floor == 2 else 0.0
    x[12] = 1.0 if payload_floor == 3 else 0.0
    return x


class TinyController:
    """Wraps ElevatorNet for production use."""

    def __init__(self):
        self._net = ElevatorNet.load()

    def predict(self, event_type: str, state, payload: dict) -> dict:
        """
        Returns dict with door_close (bool), lamp_floor (list[bool]), lamp_inside (list[bool]).
        display is always current_floor — caller sets it.
        """
        queue = list(state.request_queue)
        payload_floor = payload.get("floor", 0)
        x = encode_input(
            event_type,
            state.current_floor,
            state.door_open,
            state.door_closed,
            queue,
            payload_floor,
        )
        y = self._net.forward(x)
        return {
            "door_close": bool(y[0] > 0.5),
            "lamp_floor": [bool(y[1] > 0.5), bool(y[2] > 0.5), bool(y[3] > 0.5)],
            "lamp_inside": [bool(y[4] > 0.5), bool(y[5] > 0.5), bool(y[6] > 0.5)],
        }
