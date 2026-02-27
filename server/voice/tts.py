"""Piper TTS wrapper — local, low-latency text-to-speech.

Runs Piper as a subprocess for instant speech generation.
Falls back to a silent mode if Piper is not installed.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import shutil
import struct
import wave
from io import BytesIO
from pathlib import Path

from server.config import settings

log = logging.getLogger(__name__)


class TTSEngine:
    def __init__(self) -> None:
        self.enabled = settings.piper_enabled
        self.model = settings.piper_model
        self.sample_rate = settings.piper_rate
        self._piper_path = shutil.which("piper")

        if self.enabled and not self._piper_path:
            log.warning("Piper TTS not found in PATH. TTS disabled. Install: pip install piper-tts")
            self.enabled = False

    async def synthesize(self, text: str) -> tuple[str, float]:
        """Synthesize text to audio.

        Returns:
            (base64_wav_audio, duration_seconds)
        """
        if not self.enabled or not text.strip():
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

            # Convert raw PCM to WAV
            wav_bytes = self._pcm_to_wav(raw_audio)
            duration = len(raw_audio) / (self.sample_rate * 2)  # 16-bit = 2 bytes/sample

            audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
            return audio_b64, duration

        except Exception as e:
            log.error("TTS synthesis failed: %s", e)
            return "", 0.0

    async def synthesize_streaming(self, text: str) -> list[tuple[str, int]]:
        """Synthesize and return audio in chunks for streaming.

        Returns list of (base64_chunk, chunk_index) tuples.
        """
        audio_b64, duration = await self.synthesize(text)
        if not audio_b64:
            return []

        # For now, return as a single chunk.
        # Future: split into smaller chunks for true streaming
        return [(audio_b64, 0)]

    def estimate_duration(self, text: str) -> float:
        """Estimate speech duration from text length. ~150 words/minute."""
        word_count = len(text.split())
        return max(0.5, word_count / 2.5)  # ~2.5 words/second

    def _pcm_to_wav(self, raw_pcm: bytes) -> bytes:
        """Convert raw 16-bit PCM to WAV format."""
        buf = BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(raw_pcm)
        return buf.getvalue()
