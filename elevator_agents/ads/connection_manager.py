import asyncio
import logging
from ads.ads_interface import ADSInterface

log = logging.getLogger(__name__)

RECONNECT_DELAY = 5.0


class ConnectionManager:
    def __init__(self, net_id: str, port: int):
        self.ads = ADSInterface(net_id, port)

    async def ensure_connected(self) -> bool:
        if self.ads.connected:
            return True
        log.info("Attempting ADS reconnect...")
        success = await asyncio.to_thread(self.ads.connect)
        if not success:
            await asyncio.sleep(RECONNECT_DELAY)
        return success

    async def read_inputs(self) -> dict | None:
        if not await self.ensure_connected():
            return None
        return await asyncio.to_thread(self.ads.read_inputs)

    async def write_outputs(self, bools: dict[str, bool], display: int):
        if not await self.ensure_connected():
            return
        await asyncio.to_thread(self.ads.write_outputs, bools, display)
