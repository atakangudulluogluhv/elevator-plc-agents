import os
from dotenv import load_dotenv

load_dotenv()

ADS_NET_ID = os.getenv("ADS_NET_ID", "127.0.0.1.1.1")
ADS_PORT = int(os.getenv("ADS_PORT", "852"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

DOOR_DWELL_SECONDS = float(os.getenv("DOOR_DWELL_SECONDS", "3.0"))
ADS_POLL_INTERVAL = float(os.getenv("ADS_POLL_INTERVAL", "0.05"))

# ixButtRed is normally-closed: FALSE means emergency button pressed
BUTT_RED_ACTIVE_STATE = False

FLOOR_COUNT = 3
