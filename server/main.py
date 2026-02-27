"""Eve Avatar Engine — FastAPI server with WebSocket orchestration.

Pipeline: User Input → Memory → Dialogue FSM → LLM → Intent Router →
  [Emotion, Arc, Gesture/Choreography, Voice, Gaze, Spatial, MicroExpressions] →
  WebSocket → Client

Phase 4 additions: Memory, Emotional Arc, Dialogue State Machine, Personality, Choreography
Phase 5 additions: Advanced MicroExpressions, Input Processor, Session Telemetry
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from server.analytics.telemetry import SessionTelemetry
from server.config import settings
from server.dialogue.state_machine import DialogueStateMachine, StateContext
from server.emotion.arc import EmotionalArcTracker
from server.emotion.microexpressions import AdvancedMicroExpressionEngine
from server.emotion.model import analyze_text
from server.gesture.choreography import ChoreographyEngine
from server.gesture.engine import select_gestures, select_micro_expressions
from server.input.processor import InputProcessor
from server.intent.router import parse_llm_response, parse_streaming_chunk
from server.intent.schema import AvatarIntent, Emotion, GazeTarget, UserState
from server.llm.client import LLMClient
from server.llm.prompts import build_system_prompt
from server.memory.context import ConversationMemory
from server.personality.traits import PERSONALITY_PRESETS, DEFAULT_PERSONALITY
from server.protocol import (
    Message,
    make_arc_state_message,
    make_dialogue_state_message,
    make_intent_message,
    make_session_metrics_message,
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
    personality = PERSONALITY_PRESETS.get(settings.personality, DEFAULT_PERSONALITY)
    log.info("Eve Avatar Engine starting on %s:%s", settings.host, settings.port)
    log.info("LLM: %s @ %s", settings.llm_model, settings.llm_base_url)
    log.info("TTS: %s (enabled=%s)", settings.piper_model, settings.piper_enabled)
    log.info("Personality: %s — %s", personality.name, personality.description)
    log.info("Tracking: %s", settings.tracking_mode)
    yield
    log.info("Eve Avatar Engine shutting down")


app = FastAPI(title="Eve Avatar Engine", lifespan=lifespan)


class SessionState:
    """Per-connection session state — all Phase 1-5 subsystems."""

    def __init__(self) -> None:
        # Phase 1-3: Core systems
        self.llm = LLMClient()
        self.tts = TTSEngine()
        self.gaze_model = GazeModel()
        self.proximity_model = ProximityModel()
        self.user_anchor = UserAnchor()
        self.conversation_turn = 0
        self.is_speaking = False
        self.is_thinking = False

        # Phase 4: Advanced behavior
        self.memory = ConversationMemory(max_recent=settings.memory_max_recent_turns)
        self.emotional_arc = EmotionalArcTracker()
        self.dialogue_fsm = DialogueStateMachine()
        self.choreography = ChoreographyEngine()
        self.micro_engine = AdvancedMicroExpressionEngine()

        # Phase 4: Personality
        self.personality = PERSONALITY_PRESETS.get(settings.personality, DEFAULT_PERSONALITY)

        # Phase 5: Input processing & analytics
        self.input_processor = InputProcessor()
        self.telemetry = SessionTelemetry() if settings.telemetry_enabled else None


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session = SessionState()
    log.info("Client connected (personality=%s)", session.personality.name)

    await ws.send_text(make_status_message("connected", "Eve Avatar Engine ready").to_json())

    # Send initial dialogue state
    await ws.send_text(make_dialogue_state_message("idle").to_json())

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
        _handle_disconnect(session)
    except Exception as e:
        log.error("WebSocket error: %s", e)
        _handle_disconnect(session)


async def _handle_dialogue(ws: WebSocket, session: SessionState, user_text: str) -> None:
    """Full dialogue pipeline for one user turn — Phase 1-5 integrated."""
    turn_start = time.time()
    session.conversation_turn += 1
    session.is_thinking = True

    log.info("Turn %d: user said: %s", session.conversation_turn, user_text[:100])

    # --- Phase 4: Memory & Context ---
    session.memory.add_turn("user", user_text)

    # --- Phase 4: Dialogue FSM ---
    # Pre-analyze user text emotion for FSM
    user_emotion = analyze_text(user_text)
    fsm_context = StateContext(
        user_text=user_text,
        emotion=user_emotion,
        turn_count=session.conversation_turn,
        silence_seconds=session.memory.silence_duration,
        rapport=session.emotional_arc.state.rapport,
        active_topics=session.memory.active_topics,
    )
    prev_state = session.dialogue_fsm.current_state
    dialogue_state = session.dialogue_fsm.update(fsm_context)

    # Notify client of state change
    if dialogue_state != prev_state:
        modifiers = {
            "gestureScale": session.dialogue_fsm.modifiers.gesture_scale,
            "distanceBias": session.dialogue_fsm.modifiers.distance_bias,
            "toneHint": session.dialogue_fsm.modifiers.tone_hint,
        }
        await ws.send_text(make_dialogue_state_message(dialogue_state.value, modifiers).to_json())

        # Telemetry
        if session.telemetry:
            session.telemetry.record_state_transition(prev_state.value, dialogue_state.value)

    # --- Phase 4: Build context-aware LLM prompt ---
    arc_state = session.emotional_arc.state
    emotional_arc_str = ""
    if arc_state.valence_momentum > 0.2:
        emotional_arc_str = "The conversation is trending more positive."
    elif arc_state.valence_momentum < -0.2:
        emotional_arc_str = "The conversation is trending more serious/negative. Be sensitive."
    if arc_state.is_recovering:
        emotional_arc_str += " The user seems to be recovering from something difficult."

    system_prompt = build_system_prompt(
        personality_name=session.personality.name,
        personality_addition=session.personality.prompt_addition,
        dialogue_state=dialogue_state.value,
        user_context=session.memory.get_user_context_string(),
        emotional_arc=emotional_arc_str,
    )
    session.llm.set_system_prompt(system_prompt)

    # Send thinking status
    await ws.send_text(make_status_message("thinking").to_json())

    # --- Stream LLM response ---
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

    # --- Parse the complete response ---
    intent = parse_llm_response(accumulated)

    # Enrich with emotion analysis (fallback/reinforcement)
    text_emotion = analyze_text(intent.speech_text)
    intent.emotion.valence = intent.emotion.valence * 0.7 + text_emotion.valence * 0.3
    intent.emotion.arousal = intent.emotion.arousal * 0.7 + text_emotion.arousal * 0.3

    # --- Phase 4: Emotional arc tracking ---
    arc = session.emotional_arc.record(intent.emotion, session.conversation_turn)
    arc_modifiers = session.emotional_arc.get_behavior_modifiers()

    # Send arc state to client
    await ws.send_text(make_arc_state_message(
        rapport=arc.rapport,
        valence_momentum=arc.valence_momentum,
        dominant_emotion=arc.dominant_emotion.value,
        is_recovering=arc.is_recovering,
    ).to_json())

    if session.telemetry:
        session.telemetry.record_rapport(arc.rapport)

    # --- Phase 4: Memory - record assistant turn ---
    session.memory.add_turn(
        "assistant",
        intent.speech_text,
        emotion_primary=intent.emotion.primary.value,
        emotion_valence=intent.emotion.valence,
        emotion_arousal=intent.emotion.arousal,
    )

    # --- Phase 4: Gesture selection — choreography or single ---
    personality_mods = session.personality.modifiers
    fsm_mods = session.dialogue_fsm.modifiers

    # Try choreography first (for greetings, farewells, empathy moments)
    choreography_gestures = session.choreography.select_choreography(
        intent.emotion,
        intent.speech_text,
        dialogue_state=dialogue_state.value,
        rapport=arc.rapport,
    )

    if choreography_gestures and fsm_mods.use_choreography:
        intent.gestures = choreography_gestures
    else:
        # Standard single gesture selection
        intent.gestures = select_gestures(intent.emotion, intent.speech_text)

    # Apply personality and arc modifiers to gesture intensity
    gesture_scale = (
        personality_mods.gesture_amplitude
        * fsm_mods.gesture_scale
        * arc_modifiers["gesture_intensity"]
    )
    for g in intent.gestures:
        g.intensity = min(1.0, g.intensity * gesture_scale)

    # --- Phase 4+5: Micro-expressions (basic + advanced) ---
    basic_micros = select_micro_expressions(intent.emotion)
    advanced_micros = session.micro_engine.generate(
        current_emotion=intent.emotion,
        speech_text=intent.speech_text,
        user_text=user_text,
        turn_number=session.conversation_turn,
        rapport=arc.rapport,
    )

    # Scale micro-expression depth
    expr_depth = arc_modifiers["expression_depth"] * personality_mods.expression_intensity
    all_micros = basic_micros + advanced_micros
    for m in all_micros:
        m.weight = min(1.0, m.weight * expr_depth)
    intent.micro_expressions = all_micros

    # --- Compute gaze ---
    intent.gaze = session.gaze_model.compute_gaze(
        intent.emotion,
        session.user_anchor.state,
        is_speaking=True,
        is_thinking=False,
    )

    # Apply personality gaze modifier
    intent.gaze.weight *= personality_mods.eye_contact_duration

    # --- Compute spatial positioning ---
    spatial = session.proximity_model.compute_spatial(
        intent.emotion,
        session.conversation_turn,
        session.user_anchor.state.body_position,
    )
    if spatial:
        # Apply personality and arc distance bias
        spatial.target_distance += personality_mods.preferred_distance - 1.5  # offset from default
        spatial.target_distance += arc_modifiers.get("approach_bias", 0.0)
        spatial.target_distance += fsm_mods.distance_bias
        spatial.target_distance = max(settings.min_distance, min(settings.max_distance, spatial.target_distance))
        intent.spatial = spatial

    log.info(
        "Turn %d: state=%s emotion=%s (v=%.2f a=%.2f) rapport=%.2f gestures=%s gaze=%s",
        session.conversation_turn,
        dialogue_state.value,
        intent.emotion.primary.value,
        intent.emotion.valence,
        intent.emotion.arousal,
        arc.rapport,
        [g.gesture.value for g in intent.gestures],
        intent.gaze.target,
    )

    # --- Send the full intent ---
    await ws.send_text(make_intent_message(intent).to_json())

    # --- TTS: synthesize speech and send audio + visemes ---
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

    # --- Phase 5: Telemetry ---
    processing_time_ms = (time.time() - turn_start) * 1000
    if session.telemetry:
        session.telemetry.record_turn(
            turn_number=session.conversation_turn,
            user_text=user_text,
            response_text=intent.speech_text,
            emotion=intent.emotion,
            gestures=[g.gesture.value for g in intent.gestures],
            gaze_target=intent.gaze.target,
            dialogue_state=dialogue_state.value,
            processing_time_ms=processing_time_ms,
        )

    # Status: ready for next input
    await ws.send_text(make_status_message("ready").to_json())


def _handle_disconnect(session: SessionState) -> None:
    """Handle client disconnection — export telemetry if enabled."""
    if session.telemetry:
        metrics = session.telemetry.compute_session_metrics(
            final_rapport=session.emotional_arc.state.rapport,
        )
        log.info(
            "Session summary: %d turns, avg_valence=%.2f, avg_arousal=%.2f, "
            "peak_rapport=%.2f, avg_processing=%.1fms",
            metrics.total_turns,
            metrics.avg_valence,
            metrics.avg_arousal,
            metrics.peak_rapport,
            metrics.avg_processing_time_ms,
        )
        if settings.telemetry_export_path:
            session.telemetry.export_json(settings.telemetry_export_path)


def start() -> None:
    """Entry point for running the server."""
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    start()
