# tools/ws_server.py — V1.8 transport layer
# Async WebSocket server that receives messages from the Lemur extension.

import asyncio
import json
import websockets
from typing import Callable, Optional


class WSServer:
    """Listens on 127.0.0.1:8765. Passes each message to a handler callback."""

    def __init__(self, handler: Optional[Callable] = None,
                 host: str = "127.0.0.1", port: int = 8765):
        self.handler = handler
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        self._clients = set()
        self._stop_event = None
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_message: Optional[Callable] = None

    async def _client_loop(self, ws):
        peer = getattr(ws, "remote_address", ("?", 0))
        self._clients.add(ws)
        print(f"🔌 Extension connected: {peer}")
        if self.on_connect:
            try:
                self.on_connect(len(self._clients))
            except Exception as e:
                print(f"on_connect error: {e}")

        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    msg = {"type": "raw", "content": str(raw)[:500]}

                platform = msg.get("platform", "unknown")
                content = msg.get("content", "")
                url = msg.get("url", "")
                print(f"📨 [{platform}] {len(content)} chars from {url[:60]}")

                if self.on_message:
                    try:
                        self.on_message(platform, len(content))
                    except Exception as e:
                        print(f"on_message error: {e}")

                result = {"ok": True}
                if self.handler:
                    try:
                        result = await self.handler(msg) or {"ok": True}
                    except Exception as e:
                        print(f"handler error: {e}")
                        result = {"ok": False, "error": str(e)}

                try:
                    await ws.send(json.dumps({
                        "type": "ack",
                        "ok": result.get("ok", True),
                        "received_chars": len(content),
                        "extra": result.get("extra", {}),
                    }))
                except Exception as e:
                    print(f"send error: {e}")
        except websockets.ConnectionClosed:
            pass
        finally:
            self._clients.discard(ws)
            print(f"❌ Extension disconnected: {peer}")
            if self.on_disconnect:
                try:
                    self.on_disconnect(len(self._clients))
                except Exception as e:
                    print(f"on_disconnect error: {e}")

    async def serve(self):
        self.running = True
        self._stop_event = asyncio.Event()
        try:
            async with websockets.serve(self._client_loop, self.host, self.port,
                                        ping_interval=20, ping_timeout=10):
                print(f"🌐 WS listening on ws://{self.host}:{self.port}")
                await self._stop_event.wait()
        except OSError as e:
            print(f"⚠️ WS bind failed ({self.host}:{self.port}): {e}")
        except Exception as e:
            print(f"⚠️ WS error: {e}")
        finally:
            self.running = False
            print("🛑 WS server stopped")

    async def stop(self):
        if self._stop_event:
            self._stop_event.set()

    def client_count(self) -> int:
        return len(self._clients)
