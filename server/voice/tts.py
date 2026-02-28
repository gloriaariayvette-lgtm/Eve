"""TTS engine — supports MiniMax Speech-02-HD (Velaris's voice) and Piper (fallback).

Primary: MiniMax Speech-02-HD at api.minimaxi.chat — same "Wise Woman" voice
that Velaris uses everywhere. Gives her a consistent voice across iOS app and VR.

Fallback: Piper TTS (local subprocess) if MiniMax is unavailable or for
low-latency testing.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import shutil
import wave
from io import BytesIO

import httpx

from server.config import settings

log = logging.getLogger(__name__)


class TTSEngine:
    def __init__(self) -> None:
        self.enabled = settings.piper_enabled
        self.sample_rate = settings.piper_rate

        # MiniMax configuration
        self._minimax_enabled = bool(settings.minimax_api_key)
        self._minimax_url = settings.minimax_url
        self._minimax_api_key = settings.minimax_api_key
        self._minimax_voice = settings.minimax_voice
        self._http = httpx.AsyncClient(timeout=30.0) if self._minimax_enabled else None

        # Piper fallback
        self.model = settings.piper_model
        self._piper_path = shutil.which("piper")

        if self._minimax_enabled:
            log.info("TTS: MiniMax Speech-02-HD enabled (voice=%s)", self._minimax_voice)
            self.enabled = True
        elif self.enabled and not self._piper_path:
            log.warning("Piper TTS not found in PATH. TTS disabled. Install: pip install piper-tts")
            self.enabled = False
        elif self.enabled:
            log.info("TTS: Piper fallback (model=%s)", self.model)

    async def synthesize(self, text: str) -> tuple[str, float]:
        """Synthesize text to audio. Returns (base64_wav_audio, duration_seconds)."""
        if not self.enabled or not text.strip():
            return "", 0.0

        # Try MiniMax first
        if self._minimax_enabled:
            result = await self._synthesize_minimax(text)
            if result[0]:
                return result

            log.warning("MiniMax TTS failed, falling back to Piper")

        # Piper fallback
        return await self._synthesize_piper(text)

    async def synthesize_streaming(self, text: str) -> list[tuple[str, int]]:
        """Synthesize and return audio in chunks for streaming."""
        audio_b64, duration = await self.synthesize(text)
        if not audio_b64:
            return []
        return [(audio_b64, 0)]

    def estimate_duration(self, text: str) -> float:
        """Estimate speech duration from text length. ~150 words/minute."""
        word_count = len(text.split())
        return max(0.5, word_count / 2.5)

    async def _synthesize_minimax(self, text: str) -> tuple[str, float]:
        """Synthesize using MiniMax Speech-02-HD API."""
        try:
            headers = {
                "Authorization": f"Bearer {self._minimax_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "speech-02-hd",
                "text": text,
                "voice_setting": {
                    "voice_id": self._minimax_voice,
                },
                "audio_setting": {
                    "sample_rate": self.sample_rate,
                    "format": "wav",
                },
            }

            response = await self._http.post(
                f"{self._minimax_url}/v1/t2a_v2",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()

            # MiniMax returns audio as base64 in the response
            audio_data = data.get("data", {}).get("audio", "")
            if not audio_data:
                # Some API versions return raw bytes
                if response.headers.get("content-type", "").startswith("audio/"):
                    audio_data = base64.b64encode(response.content).decode("ascii")

            if audio_data:
                # Estimate duration from audio size
                try:
                    raw = base64.b64decode(audio_data)
                    duration = len(raw) / (self.sample_rate * 2)  # 16-bit mono
                except Exception:
                    duration = self.estimate_duration(text)

                return audio_data, duration

            return "", 0.0

        except Exception as e:
            log.error("MiniMax TTS error: %s", e)
            return "", 0.0

    async def _synthesize_piper(self, text: str) -> tuple[str, float]:
        """Synthesize using local Piper TTS."""
        if not self._piper_path:
            return "", 0.0

        try:
            proc = await asyncio.create_subprocess_exec(
                self._piper_path,
                "--model", self.model,
                "--output-raw",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            raw_audio, stderr = await proc.communicate(text.encode("utf-8"))

            if proc.returncode != 0:
                log.error("Piper TTS error: %s", stderr.decode())
                return "", 0.0

            wav_bytes = self._pcm_to_wav(raw_audio)
            duration = len(raw_audio) / (self.sample_rate * 2)

            audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
            return audio_b64, duration

        except Exception as e:
            log.error("Piper TTS error: %s", e)
            return "", 0.0

    def _pcm_to_wav(self, raw_pcm: bytes) -> bytes:
        """Convert raw 16-bit PCM to WAV format."""
        buf = BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(raw_pcm)
        return buf.getvalue()
