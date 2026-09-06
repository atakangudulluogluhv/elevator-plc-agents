import pyads
import logging
from typing import Optional
from ads.variable_map import ALL_INPUTS, BOOL_OUTPUTS, OUT_DISPLAY, TYPE_BOOL, TYPE_UINT

log = logging.getLogger(__name__)


class ADSInterface:
    def __init__(self, net_id: str, port: int):
        self._net_id = net_id
        self._port = port
        self._plc: Optional[pyads.Connection] = None

    def connect(self) -> bool:
        try:
            self._plc = pyads.Connection(self._net_id, self._port)
            self._plc.open()
            log.info("ADS connected to %s:%d", self._net_id, self._port)
            return True
        except pyads.ADSError as e:
            log.error("ADS connect failed: %s", e)
            self._plc = None
            return False

    def disconnect(self):
        if self._plc:
            try:
                self._plc.close()
            except Exception:
                pass
            self._plc = None

    @property
    def connected(self) -> bool:
        return self._plc is not None

    def read_inputs(self) -> Optional[dict]:
        if not self._plc:
            return None
        try:
            result = {}
            for sym in ALL_INPUTS:
                result[sym] = self._plc.read_by_name(sym, TYPE_BOOL)
            return result
        except pyads.ADSError as e:
            log.warning("ADS read failed: %s", e)
            self.disconnect()
            return None

    def write_outputs(self, bools: dict[str, bool], display: int):
        if not self._plc:
            return
        try:
            for sym, val in bools.items():
                self._plc.write_by_name(sym, val, TYPE_BOOL)
            self._plc.write_by_name(OUT_DISPLAY, display, TYPE_UINT)
        except pyads.ADSError as e:
            log.warning("ADS write failed: %s", e)
            self.disconnect()

    def write_safe_defaults(self):
        """All outputs to safe state (motor off, door not forced closed)."""
        safe_bools = {sym: False for sym in BOOL_OUTPUTS}
        if self._plc:
            try:
                for sym, val in safe_bools.items():
                    self._plc.write_by_name(sym, val, TYPE_BOOL)
                self._plc.write_by_name(OUT_DISPLAY, 0, TYPE_UINT)
            except Exception:
                pass
