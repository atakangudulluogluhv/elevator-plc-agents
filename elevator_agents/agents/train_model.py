"""
Generate training data from deterministic elevator rules and train the tiny MLP.
Run once: python agents/train_model.py
Saves agents/elevator_net.npz (~10K parameters).

Rules encoded here:
  BUTTON_PRESSED  -> door_close=True, lamps=queue (queue already includes pressed floor)
  DOOR_FULLY_OPEN -> door_close=True, lamps=queue (unchanged)
"""
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.tiny_controller import encode_input, MODEL_PATH

N_HIDDEN = 90
N_IN = 13
N_OUT = 7
LR = 0.05
EPOCHS = 500
RNG_SEED = 42


def _sigmoid(x):
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))


def _relu(x):
    return np.maximum(0.0, x)


def _relu_grad(x):
    return (x > 0.0).astype(np.float32)


def generate_data():
    X, Y = [], []
    floors = [1, 2, 3]

    for event_type in ("BUTTON_PRESSED", "DOOR_FULLY_OPEN"):
        for current_floor in floors:
            for door_open in (True, False):
                for door_closed in (True, False):
                    if door_open and door_closed:
                        continue  # physically impossible
                    for q_mask in range(8):
                        base_queue = [f for f in floors if q_mask & (1 << (f - 1))]

                        if event_type == "BUTTON_PRESSED":
                            for payload_floor in floors:
                                # state machine adds pressed floor before event fires
                                queue = sorted(set(base_queue) | {payload_floor})
                                x = encode_input(event_type, current_floor, door_open,
                                                 door_closed, queue, payload_floor)
                                lamps = [1.0 if f in queue else 0.0 for f in floors]
                                # door_close=1, lamp_floor×3, lamp_inside×3
                                y = [1.0] + lamps + lamps
                                X.append(x)
                                Y.append(y)
                        else:  # DOOR_FULLY_OPEN
                            x = encode_input(event_type, current_floor, door_open,
                                             door_closed, base_queue, 0)
                            lamps = [1.0 if f in base_queue else 0.0 for f in floors]
                            y = [1.0] + lamps + lamps
                            X.append(x)
                            Y.append(y)

    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)


def forward(params, X):
    W1, b1, W2, b2, W3, b3 = params
    Z1 = X @ W1.T + b1          # (N, 90)
    A1 = _relu(Z1)
    Z2 = A1 @ W2.T + b2         # (N, 90)
    A2 = _relu(Z2)
    Z3 = A2 @ W3.T + b3         # (N, 7)
    Y_hat = _sigmoid(Z3)
    return Y_hat, (Z1, A1, Z2, A2, Z3)


def bce_loss(Y_hat, Y):
    eps = 1e-7
    return -np.mean(Y * np.log(Y_hat + eps) + (1 - Y) * np.log(1 - Y_hat + eps))


def backward(params, X, Y, Y_hat, cache):
    W1, b1, W2, b2, W3, b3 = params
    Z1, A1, Z2, A2, Z3 = cache
    N = X.shape[0]

    dZ3 = (Y_hat - Y) / N                     # (N, 7)
    dW3 = dZ3.T @ A2                           # (7, 90)
    db3 = dZ3.sum(axis=0)                      # (7,)

    dA2 = dZ3 @ W3                             # (N, 90)
    dZ2 = dA2 * _relu_grad(Z2)
    dW2 = dZ2.T @ A1                           # (90, 90)
    db2 = dZ2.sum(axis=0)                      # (90,)

    dA1 = dZ2 @ W2                             # (N, 90)
    dZ1 = dA1 * _relu_grad(Z1)
    dW1 = dZ1.T @ X                            # (90, 13)
    db1 = dZ1.sum(axis=0)                      # (90,)

    return dW1, db1, dW2, db2, dW3, db3


def train():
    X, Y = generate_data()
    print(f"Training samples: {len(X)}")

    rng = np.random.default_rng(RNG_SEED)
    scale1 = np.sqrt(2.0 / N_IN)
    scale2 = np.sqrt(2.0 / N_HIDDEN)

    W1 = rng.standard_normal((N_HIDDEN, N_IN)).astype(np.float32) * scale1
    b1 = np.zeros(N_HIDDEN, dtype=np.float32)
    W2 = rng.standard_normal((N_HIDDEN, N_HIDDEN)).astype(np.float32) * scale2
    b2 = np.zeros(N_HIDDEN, dtype=np.float32)
    W3 = rng.standard_normal((N_OUT, N_HIDDEN)).astype(np.float32) * scale2
    b3 = np.zeros(N_OUT, dtype=np.float32)

    params = [W1, b1, W2, b2, W3, b3]

    for epoch in range(1, EPOCHS + 1):
        Y_hat, cache = forward(params, X)
        loss = bce_loss(Y_hat, Y)
        grads = backward(params, X, Y, Y_hat, cache)

        for i in range(len(params)):
            params[i] -= LR * grads[i]

        if epoch % 50 == 0 or epoch == 1:
            preds = (Y_hat > 0.5).astype(np.float32)
            acc = (preds == Y).all(axis=1).mean()
            print(f"Epoch {epoch:4d}  loss={loss:.5f}  exact_match={acc:.3f}")

    Y_hat, _ = forward(params, X)
    preds = (Y_hat > 0.5).astype(np.float32)
    acc = (preds == Y).all(axis=1).mean()
    print(f"\nFinal exact-match accuracy: {acc * 100:.1f}%")

    W1, b1, W2, b2, W3, b3 = params
    total = W1.size + b1.size + W2.size + b2.size + W3.size + b3.size
    print(f"Total parameters: {total:,}")

    np.savez(MODEL_PATH, W1=W1, b1=b1, W2=W2, b2=b2, W3=W3, b3=b3)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
