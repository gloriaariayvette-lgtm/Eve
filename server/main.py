"""Eve Avatar Engine — FastAPI server with WebSocket orchestration.

Pipeline: User Input → LLM → Intent Router → [Emotion, Gesture, Voice, Gaze, Spatial] → WebSocket → Client
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from server.config import settings
from server.emotion.model import analyze_text
from server.gesture.engine import select_gestures, select_micro_expressions
from server.intent.router import parse_llm_response, parse_streaming_chunk
from server.intent.schema import AvatarIntent, Emotion, GazeTarget, UserState
from server.llm.client import LLMClient
from server.protocol import (
    Message,
    make_intent_message,
    make_speech_audio_message,
    make_speech_end_message,
    make_speech_start_message,
    make_status_message,
    make_viseme_message,
    parse_user_input,
    parse_user_tracking,
)
from server.spatial.anchor import UserAnchor
from server.spatial.gaze import GazeModel
from server.spatial.proximity import ProximityModel
from server.voice.tts import TTSEngine
from server.voice.viseme import generate_visemes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("eve")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Eve Avatar Engine starting on %s:%s", settings.host, settings.port)
    log.info("LLM: %s @ %s", settings.llm_model, settings.llm_base_url)
    log.info("TTS: %s (enabled=%s)", settings.piper_model, settings.piper_enabled)
    log.info("Tracking: %s", settings.tracking_mode)
    yield
    log.info("Eve Avatar Engine shutting down")


app = FastAPI(title="Eve Avatar Engine", lifespan=lifespan)


class SessionState:
    """Per-connection session state."""

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.tts = TTSEngine()
        self.gaze_model = GazeModel()
        self.proximity_model = ProximityModel()
        self.user_anchor = UserAnchor()
        self.conversation_turn = 0
        self.is_speaking = False
        self.is_thinking = False


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session = SessionState()
    log.info("Client connected")

    await ws.send_text(make_status_message("connected", "Eve Avatar Engine ready").to_json())

    try:
        while True:
            raw = await ws.receive_text()
            msg = Message.from_json(raw)

            if msg.type == "user_input":
                text = parse_user_input(msg)
                if text.strip():
                    # Process in background so we can keep receiving tracking data
                    asyncio.create_task(_handle_dialogue(ws, session, text))

            elif msg.type == "user_tracking":
                tracking = parse_user_tracking(msg)
                session.user_anchor.update(tracking)

            elif msg.type == "ping":
                await ws.send_text(Message(type="pong").to_json())

    except WebSocketDisconnect:
        log.info("Client disconnected")
    except Exception as e:
        log.error("WebSocket error: %s", e)


async def _handle_dialogue(ws: WebSocket, session: SessionState, user_text: str) -> None:
    """Full dialogue pipeline for one user turn."""
    session.conversation_turn += 1
    session.is_thinking = True

    log.info("Turn %d: user said: %s", session.conversation_turn, user_text[:100])

    # Send thinking status
    await ws.send_text(make_status_message("thinking").to_json())

    # Stream LLM response
    accumulated = ""
    early_intent_sent = False

    async for chunk in session.llm.chat_stream(user_text):
        accumulated += chunk

        # Try to parse early intent (emotion/gesture before speech is done)
        if not early_intent_sent:
            early_intent = parse_streaming_chunk(accumulated)
            if early_intent:
                # Send early emotion/gaze update (no speech yet)
                early_intent.speech_text = ""
                gaze = session.gaze_model.compute_gaze(
                    early_intent.emotion,
                    session.user_anchor.state,
                    is_speaking=False,
                    is_thinking=True,
                )
                early_intent.gaze = gaze
                await ws.send_text(make_intent_message(early_intent).to_json())
                early_intent_sent = True

    session.is_thinking = False

    # Parse the complete response
    intent = parse_llm_response(accumulated)

    # Enrich with emotion analysis (fallback/reinforcement)
    text_emotion = analyze_text(intent.speech_text)
    # Blend LLM-tagged emotion with text analysis
    intent.emotion.valence = intent.emotion.valence * 0.7 + text_emotion.valence * 0.3
    intent.emotion.arousal = intent.emotion.arousal * 0.7 + text_emotion.arousal * 0.3

    # Generate gestures from emotion + speech
    intent.gestures = select_gestures(intent.emotion, intent.speech_text)

    # Generate micro-expressions
    intent.micro_expressions = select_micro_expressions(intent.emotion)

    # Compute gaze
    intent.gaze = session.gaze_model.compute_gaze(
        intent.emotion,
        session.user_anchor.state,
        is_speaking=True,
        is_thinking=False,
    )

    # Compute spatial positioning
    spatial = session.proximity_model.compute_spatial(
        intent.emotion,
        session.conversation_turn,
        session.user_anchor.state.body_position,
    )
    if spatial:
        intent.spatial = spatial

    log.info(
        "Turn %d: emotion=%s (v=%.2f a=%.2f), gestures=%s, gaze=%s",
        session.conversation_turn,
        intent.emotion.primary.value,
        intent.emotion.valence,
        intent.emotion.arousal,
        [g.gesture.value for g in intent.gestures],
        intent.gaze.target,
    )

    # Send the full intent (emotion, gestures, gaze, spatial)
    await ws.send_text(make_intent_message(intent).to_json())

    # TTS: synthesize speech and send audio + visemes
    if intent.speech_text and session.tts.enabled:
        session.is_speaking = True
        duration_est = session.tts.estimate_duration(intent.speech_text)

        await ws.send_text(make_speech_start_message(intent.speech_text, duration_est).to_json())

        # Generate visemes
        visemes = generate_visemes(intent.speech_text, duration_est)
        if visemes:
            await ws.send_text(make_viseme_message(visemes).to_json())

        # Synthesize audio
        chunks = await session.tts.synthesize_streaming(intent.speech_text)
        for audio_b64, chunk_idx in chunks:
            await ws.send_text(
                make_speech_audio_message(audio_b64, session.tts.sample_rate, chunk_idx).to_json()
            )

        await ws.send_text(make_speech_end_message().to_json())
        session.is_speaking = False

    elif intent.speech_text:
        # TTS disabled — still send speech text and estimated duration for client-side handling
        duration_est = session.tts.estimate_duration(intent.speech_text)
        await ws.send_text(make_speech_start_message(intent.speech_text, duration_est).to_json())

        visemes = generate_visemes(intent.speech_text, duration_est)
        if visemes:
            await ws.send_text(make_viseme_message(visemes).to_json())

        await ws.send_text(make_speech_end_message().to_json())

    # Status: ready for next input
    await ws.send_text(make_status_message("ready").to_json())


def start() -> None:
    """Entry point for running the server."""
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    start()
