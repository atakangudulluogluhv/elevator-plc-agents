"""
Quick ADS connection test — run this standalone to verify pyads can read PLC variables.
Usage: python test_ads.py
"""
import sys
import time

try:
    import pyads
except ImportError:
    print("ERROR: pyads not installed. Run: pip install pyads")
    sys.exit(1)

from config import ADS_NET_ID, ADS_PORT
from ads.variable_map import ALL_INPUTS

print(f"Connecting to {ADS_NET_ID}:{ADS_PORT} ...")
plc = pyads.Connection(ADS_NET_ID, ADS_PORT)
try:
    plc.open()
    print("Connected!\n")
    print("Reading inputs every second (Ctrl+C to stop):\n")
    while True:
        for sym in ALL_INPUTS:
            val = plc.read_by_name(sym, pyads.PLCTYPE_BOOL)
            print(f"  {sym:<35} = {val}")
        print("-" * 50)
        time.sleep(1.0)
except pyads.ADSError as e:
    print(f"ADS Error: {e}")
    print("\nTips:")
    print("  - Is TwinCAT running? Check XAE/XAR status.")
    print(f"  - Is PLCStudent (port {ADS_PORT}) active?")
    print(f"  - Is AMS NetId correct? ({ADS_NET_ID})")
    print("  - Check Windows Firewall / TwinCAT ADS route.")
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    plc.close()
