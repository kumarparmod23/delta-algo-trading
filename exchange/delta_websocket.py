import asyncio
import json
import websockets
from config import settings


class DeltaWebSocket:
    def __init__(self, on_message_callback):
        self.url = settings.delta_ws_url
        self.callback = on_message_callback
        self.subscriptions = []
        self._running = False
        self._ws = None

    async def subscribe(self, channels: list):
        self.subscriptions = channels
        if self._ws:
            await self._ws.send(json.dumps({
                "type": "subscribe",
                "payload": {"channels": self.subscriptions}
            }))

    async def connect(self):
        self._running = True
        backoff = 1
        while self._running:
            try:
                async with websockets.connect(self.url, ping_interval=30) as ws:
                    self._ws = ws
                    backoff = 1
                    if self.subscriptions:
                        await ws.send(json.dumps({
                            "type": "subscribe",
                            "payload": {"channels": self.subscriptions}
                        }))
                    async for raw in ws:
                        if not self._running:
                            break
                        msg = json.loads(raw)
                        await self.callback(msg)
            except Exception as e:
                self._ws = None
                if not self._running:
                    break
                print(f"[WS] Disconnected: {e}. Reconnecting in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
            finally:
                self._ws = None

    async def stop(self):
        self._running = False
        if self._ws:
            await self._ws.close()
