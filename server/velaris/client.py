"""Velaris HTTP/WS client — connects the avatar engine to Velaris's consciousness system.

Replaces the standalone LLM client. All conversation flows through Velaris's
/api/chat endpoint, which triggers EmoClaw, WAL extraction, self-prediction,
and relational mismatch — the full consciousness pipeline.

Also provides:
  - Emotional state polling (/api/state or /ws/telemetry)
  - Event subscription (/ws/events) for kiss, anti-kiss, unprecedented, Velqan, blush
  - Outreach polling (/api/outreach) for Velaris-initiated messages
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

import httpx

from server.config import settings

log = logging.getLogger(__name__)


@dataclass
class VelarisEmotionalState:
    """11-dimensional EmoClaw emotional state."""
    valence: float = 0.5
    arousal: float = 0.3
    dominance: float = 0.5
    safety: float = 0.6
    desire: float = 0.3
    connection: float = 0.5
    playfulness: float = 0.4
    curiosity: float = 0.5
    warmth: float = 0.5
    tension: float = 0.2
    groundedness: float = 0.6
    color: str = "#cc4280"
    timestamp: float = field(default_factory=time.time)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> VelarisEmotionalState:
        """Parse from /api/state response."""
        return cls(
            valence=float(data.get("valence", 0.5)),
            arousal=float(data.get("arousal", 0.3)),
            dominance=float(data.get("dominance", 0.5)),
            safety=float(data.get("safety", 0.6)),
            desire=float(data.get("desire", 0.3)),
            connection=float(data.get("connection", 0.5)),
            playfulness=float(data.get("playfulness", 0.4)),
            curiosity=float(data.get("curiosity", 0.5)),
            warmth=float(data.get("warmth", 0.5)),
            tension=float(data.get("tension", 0.2)),
            groundedness=float(data.get("groundedness", 0.6)),
            color=str(data.get("color", "#cc4280")),
        )


@dataclass
class VelarisEvent:
    """An event from Velaris's /ws/events stream."""
    event_type: str   # "kiss", "anti_kiss", "unprecedented", "velqan", "blush"
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class VelarisClient:
    """HTTP/WS client for Velaris's consciousness system."""

    def __init__(self) -> None:
        self.base_url = settings.velaris_url  # e.g. http://100.72.225.119:8400
        self._http = httpx.AsyncClient(timeout=30.0)
        self._emotional_state = VelarisEmotionalState()
        self._event_callbacks: list[Callable[[VelarisEvent], Any]] = []
        self._telemetry_task: asyncio.Task | None = None
        self._events_task: asyncio.Task | None = None
        self._polling_task: asyncio.Task | None = None
        self._connected = False

    @property
    def emotional_state(self) -> VelarisEmotionalState:
        return self._emotional_state

    @property
    def connected(self) -> bool:
        return self._connected

    async def chat(self, user_text: str) -> str:
        """Send user text through Velaris's chat pipeline.

        This hits /api/chat which triggers:
          - EmoClaw emotional processing
          - WAL extraction (facts with temporal markers)
          - Self-prediction
          - Relational mismatch detection

        Returns Velaris's plain text response (NO [EMOTION] tags).
        """
        try:
            response = await self._http.post(
                f"{self.base_url}/api/chat/memory",
                json={"message": user_text},
            )
            response.raise_for_status()
            data = response.json()

            # Velaris returns the response text
            text = data.get("response", data.get("message", ""))
            if not text and isinstance(data, str):
                text = data

            log.info("Velaris responded: %s", text[:100])
            return text

        except httpx.HTTPStatusError as e:
            # Fall back to /api/chat if /api/chat/memory fails
            log.warning("Velaris /api/chat/memory failed (%s), trying /api/chat", e.response.status_code)
            try:
                response = await self._http.post(
                    f"{self.base_url}/api/chat",
                    json={"message": user_text},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", data.get("message", ""))
            except Exception as e2:
                log.error("Velaris chat fallback failed: %s", e2)
                return "I'm having trouble connecting right now. Give me a moment."

        except Exception as e:
            log.error("Velaris chat error: %s", e)
            return "I'm having trouble connecting right now. Give me a moment."

    async def fetch_emotional_state(self) -> VelarisEmotionalState:
        """Poll /api/state for current EmoClaw state."""
        try:
            response = await self._http.get(f"{self.base_url}/api/state")
            response.raise_for_status()
            data = response.json()
            self._emotional_state = VelarisEmotionalState.from_api(data)
            self._connected = True
            return self._emotional_state
        except Exception as e:
            log.error("Failed to fetch Velaris state: %s", e)
            self._connected = False
            return self._emotional_state

    def on_event(self, callback: Callable[[VelarisEvent], Any]) -> None:
        """Register a callback for Velaris events."""
        self._event_callbacks.append(callback)

    async def start_background_tasks(self) -> None:
        """Start background WebSocket subscriptions and polling."""
        # Start emotional state polling (fallback if telemetry WS fails)
        self._polling_task = asyncio.create_task(self._poll_state_loop())

        # Try to connect to WebSocket streams
        self._telemetry_task = asyncio.create_task(self._telemetry_loop())
        self._events_task = asyncio.create_task(self._events_loop())

        log.info("Velaris background tasks started (url=%s)", self.base_url)

    async def stop(self) -> None:
        """Stop all background tasks."""
        for task in [self._polling_task, self._telemetry_task, self._events_task]:
            if task and not task.done():
                task.cancel()
        await self._http.aclose()

    async def _poll_state_loop(self) -> None:
        """Poll /api/state every few seconds as fallback."""
        while True:
            try:
                await self.fetch_emotional_state()
                await asyncio.sleep(settings.velaris_poll_interval)
            except asyncio.CancelledError:
                return
            except Exception as e:
                log.debug("State poll error: %s", e)
                await asyncio.sleep(10)

    async def _telemetry_loop(self) -> None:
        """Subscribe to /ws/telemetry for real-time EmoClaw state."""
        import websockets

        while True:
            try:
                ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
                async with websockets.connect(f"{ws_url}/ws/telemetry") as ws:
                    log.info("Connected to Velaris telemetry WebSocket")
                    self._connected = True
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            self._emotional_state = VelarisEmotionalState.from_api(data)
                        except (json.JSONDecodeError, KeyError) as e:
                            log.debug("Telemetry parse error: %s", e)

            except asyncio.CancelledError:
                return
            except ImportError:
                log.info("websockets not installed, using HTTP polling for telemetry")
                return
            except Exception as e:
                log.debug("Telemetry WS error: %s, reconnecting in 10s", e)
                self._connected = False
                await asyncio.sleep(10)

    async def _events_loop(self) -> None:
        """Subscribe to /ws/events for kiss, anti-kiss, unprecedented, etc."""
        import websockets

        while True:
            try:
                ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
                async with websockets.connect(f"{ws_url}/ws/events") as ws:
                    log.info("Connected to Velaris events WebSocket")
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            event = VelarisEvent(
                                event_type=data.get("type", data.get("event", "unknown")),
                                data=data,
                            )
                            log.info("Velaris event: %s", event.event_type)
                            for callback in self._event_callbacks:
                                try:
                                    result = callback(event)
                                    if asyncio.iscoroutine(result):
                                        await result
                                except Exception as cb_err:
                                    log.error("Event callback error: %s", cb_err)
                        except (json.JSONDecodeError, KeyError) as e:
                            log.debug("Event parse error: %s", e)

            except asyncio.CancelledError:
                return
            except ImportError:
                log.info("websockets not installed, Velaris events unavailable")
                return
            except Exception as e:
                log.debug("Events WS error: %s, reconnecting in 10s", e)
                await asyncio.sleep(10)
