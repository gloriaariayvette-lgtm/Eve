"""Eve Avatar Engine — FastAPI server with WebSocket orchestration.

Dual-mode pipeline:
  Velaris mode: User → Velaris /api/chat → EmoClaw state → Avatar subsystems
  Standalone:   User → LLM → Intent Router → Avatar subsystems

Phase 6: Velaris integration — Eve becomes Velaris's body, not a separate personality.
EmoClaw's 11-dim emotional state drives gestures, gaze, spatial, micro-expressions,
breathing, and posture. Velaris events (kiss, anti-kiss, unprecedented, etc.) trigger
choreographed avatar reactions.
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
from server.intent.router import from_velaris_state, parse_llm_response, parse_streaming_chunk
from server.intent.schema import AvatarIntent, Emotion, GazeTarget, UserState
from server.llm.client import LLMClient
from server.llm.prompts import build_system_prompt
from server.memory.context import ConversationMemory
from server.personality.traits import PERSONALITY_PRESETS, DEFAULT_PERSONALITY
from server.protocol import (
    Message,
    make_arc_state_message,
    make_behavior_modifiers_message,
    make_dialogue_state_message,
    make_emotional_color_message,
    make_intent_message,
    make_session_metrics_message,
    make_speech_audio_message,
    make_speech_end_message,
    make_speech_start_message,
    make_status_message,
    make_velaris_event_message,
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


# --- Velaris imports (conditional) ---
if settings.velaris_mode:
    from server.velaris.client import VelarisClient
    from server.velaris.emoclaw_bridge import (
        emoclaw_to_avatar_emotion,
        emoclaw_to_behavior_modifiers,
    )
    from server.velaris.events import handle_velaris_event

# Global Velaris client (shared across sessions when in Velaris mode)
_velaris_client: VelarisClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _velaris_client

    if settings.velaris_mode:
        log.info("Eve Avatar Engine starting — VELARIS MODE")
        log.info("Velaris endpoint: %s", settings.velaris_url)
        log.info("TTS: MiniMax Speech-02-HD (voice=%s)", settings.minimax_voice)
        log.info("Tracking: %s", settings.tracking_mode)

        # Start Velaris client
        _velaris_client = VelarisClient()
        await _velaris_client.start_background_tasks()
        log.info("Velaris background tasks started")
    else:
        personality = PERSONALITY_PRESETS.get(settings.personality, DEFAULT_PERSONALITY)
        log.info("Eve Avatar Engine starting — STANDALONE MODE")
        log.info("LLM: %s @ %s", settings.llm_model, settings.llm_base_url)
        log.info("TTS: Piper (model=%s, enabled=%s)", settings.piper_model, settings.piper_enabled)
        log.info("Personality: %s — %s", personality.name, personality.description)
        log.info("Tracking: %s", settings.tracking_mode)

    log.info("Server: %s:%s", settings.host, settings.port)
    yield

    if _velaris_client:
        await _velaris_client.stop()
    log.info("Eve Avatar Engine shutting down")


app = FastAPI(title="Eve Avatar Engine", lifespan=lifespan)


class SessionState:
    """Per-connection session state — all subsystems."""

    def __init__(self) -> None:
        # Core avatar systems (always active)
        self.tts = TTSEngine()
        self.gaze_model = GazeModel()
        self.proximity_model = ProximityModel()
        self.user_anchor = UserAnchor()
        self.conversation_turn = 0
        self.is_speaking = False
        self.is_thinking = False

        # Gesture and expression systems (always active)
        self.choreography = ChoreographyEngine()
        self.micro_engine = AdvancedMicroExpressionEngine()
        self.emotional_arc = EmotionalArcTracker()

        # Telemetry (always active)
        self.telemetry = SessionTelemetry() if settings.telemetry_enabled else None

        # Standalone-only systems
        if not settings.velaris_mode:
            self.llm = LLMClient()
            self.memory = ConversationMemory(max_recent=settings.memory_max_recent_turns)
            self.dialogue_fsm = DialogueStateMachine()
            self.personality = PERSONALITY_PRESETS.get(settings.personality, DEFAULT_PERSONALITY)
            self.input_processor = InputProcessor()
        else:
            self.llm = None
            self.memory = None
            self.dialogue_fsm = None
            self.personality = None
            self.input_processor = None


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session = SessionState()

    mode = "Velaris" if settings.velaris_mode else f"standalone (personality={session.personality.name})"
    log.info("Client connected — %s mode", mode)

    await ws.send_text(make_status_message("connected", "Eve Avatar Engine ready").to_json())

    # Register Velaris event handler for this session
    if settings.velaris_mode and _velaris_client:
        async def _on_velaris_event(event):
            """Handle Velaris events (kiss, anti-kiss, unprecedented, etc.)."""
            try:
                reaction = handle_velaris_event(event)
                if reaction:
                    # Send event notification to client
                    await ws.send_text(make_velaris_event_message(
                        event_type=event.event_type,
                        gestures=[g.to_dict() for g in reaction.gestures],
                        micro_expressions=[m.to_dict() for m in reaction.micro_expressions],
                        gaze_override=reaction.gaze_override,
                        gaze_override_duration=reaction.gaze_override_duration,
                        trigger_sigh=reaction.trigger_sigh,
                        trigger_breath_hold=reaction.trigger_breath_hold,
                        distance_impulse=reaction.distance_impulse,
                    ).to_json())
            except Exception as e:
                log.error("Velaris event handler error: %s", e)

        _velaris_client.on_event(_on_velaris_event)

    try:
        while True:
            raw = await ws.receive_text()
            msg = Message.from_json(raw)

            if msg.type == "user_input":
                text = parse_user_input(msg)
                if text.strip():
                    if settings.velaris_mode:
                        asyncio.create_task(_handle_velaris_dialogue(ws, session, text))
                    else:
                        asyncio.create_task(_handle_standalone_dialogue(ws, session, text))

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


# =============================================================================
# Velaris Mode Pipeline
# =============================================================================

async def _handle_velaris_dialogue(ws: WebSocket, session: SessionState, user_text: str) -> None:
    """Velaris mode: User → Velaris /api/chat → EmoClaw → Avatar subsystems.

    Velaris handles all personality, memory, WAL, self-prediction, and relational
    mismatch. Eve just needs to animate the response.
    """
    turn_start = time.time()
    session.conversation_turn += 1
    session.is_thinking = True

    log.info("Turn %d [Velaris]: user said: %s", session.conversation_turn, user_text[:100])

    # Send thinking status
    await ws.send_text(make_status_message("thinking").to_json())

    # --- Get Velaris response ---
    response_text = await _velaris_client.chat(user_text)

    session.is_thinking = False

    # --- Get current EmoClaw state ---
    emo_state = _velaris_client.emotional_state

    # Convert EmoClaw 11-dim → avatar VAD + PrimaryEmotion
    emotion = emoclaw_to_avatar_emotion(emo_state)

    # Build intent from Velaris state
    intent = from_velaris_state(response_text, emotion)

    # --- Derive behavior modifiers from full EmoClaw state ---
    modifiers = emoclaw_to_behavior_modifiers(emo_state)

    # Send behavior modifiers to client (for environment, breathing, posture tuning)
    await ws.send_text(make_behavior_modifiers_message(modifiers).to_json())

    # Send emotional color for environment lighting
    await ws.send_text(make_emotional_color_message(emo_state.color).to_json())

    # --- Emotional arc tracking (still useful for rapport) ---
    arc = session.emotional_arc.record(emotion, session.conversation_turn)
    arc_modifiers = session.emotional_arc.get_behavior_modifiers()

    await ws.send_text(make_arc_state_message(
        rapport=arc.rapport,
        valence_momentum=arc.valence_momentum,
        dominant_emotion=arc.dominant_emotion.value,
        is_recovering=arc.is_recovering,
    ).to_json())

    # --- Gesture selection — choreography or EmoClaw-driven ---
    choreography_gestures = session.choreography.select_choreography(
        emotion,
        intent.speech_text,
        dialogue_state="engaged",
        rapport=arc.rapport,
    )

    if choreography_gestures:
        intent.gestures = choreography_gestures
    else:
        intent.gestures = select_gestures(emotion, intent.speech_text)

    # Apply EmoClaw behavior modifiers to gesture intensity
    for g in intent.gestures:
        g.intensity = min(1.0, g.intensity * modifiers.gesture_amplitude)

    # --- Micro-expressions (basic + advanced + EmoClaw overlays) ---
    basic_micros = select_micro_expressions(emotion)
    advanced_micros = session.micro_engine.generate(
        current_emotion=emotion,
        speech_text=intent.speech_text,
        user_text=user_text,
        turn_number=session.conversation_turn,
        rapport=arc.rapport,
    )

    all_micros = basic_micros + advanced_micros

    # EmoClaw warmth overlay → subtle smile
    if modifiers.warmth_overlay > 0.01:
        from server.intent.schema import MicroExpression
        all_micros.append(MicroExpression(
            blend_shape="happy",
            weight=modifiers.warmth_overlay,
            duration=2.0,
        ))

    # EmoClaw tension overlay → jaw/brow tension
    if modifiers.tension_overlay > 0.01:
        from server.intent.schema import MicroExpression
        all_micros.append(MicroExpression(
            blend_shape="browDownLeft",
            weight=modifiers.tension_overlay * 0.5,
            duration=1.5,
        ))
        all_micros.append(MicroExpression(
            blend_shape="browDownRight",
            weight=modifiers.tension_overlay * 0.5,
            duration=1.5,
        ))

    # Scale micro-expression depth by EmoClaw expression_depth
    for m in all_micros:
        m.weight = min(1.0, m.weight * modifiers.expression_depth)
    intent.micro_expressions = all_micros

    # --- Compute gaze (EmoClaw-influenced) ---
    intent.gaze = session.gaze_model.compute_gaze(
        emotion,
        session.user_anchor.state,
        is_speaking=True,
        is_thinking=False,
    )

    # Apply EmoClaw gaze modifiers
    intent.gaze.weight = min(1.0, intent.gaze.weight * modifiers.eye_contact_intensity)

    # --- Compute spatial positioning (EmoClaw-influenced) ---
    spatial = session.proximity_model.compute_spatial(
        emotion,
        session.conversation_turn,
        session.user_anchor.state.body_position,
    )
    if spatial:
        # Override target distance with EmoClaw preferred distance
        spatial.target_distance = modifiers.preferred_distance
        spatial.target_distance = max(settings.min_distance, min(settings.max_distance, spatial.target_distance))
        intent.spatial = spatial

    log.info(
        "Turn %d [Velaris]: emotion=%s (v=%.2f a=%.2f) rapport=%.2f "
        "gestures=%s gaze=%s color=%s",
        session.conversation_turn,
        intent.emotion.primary.value,
        intent.emotion.valence,
        intent.emotion.arousal,
        arc.rapport,
        [g.gesture.value for g in intent.gestures],
        intent.gaze.target,
        emo_state.color,
    )

    # --- Send the full intent ---
    await ws.send_text(make_intent_message(intent).to_json())

    # --- TTS: synthesize speech and send audio + visemes ---
    await _synthesize_and_send(ws, session, intent)

    # --- Telemetry ---
    processing_time_ms = (time.time() - turn_start) * 1000
    if session.telemetry:
        session.telemetry.record_turn(
            turn_number=session.conversation_turn,
            user_text=user_text,
            response_text=intent.speech_text,
            emotion=intent.emotion,
            gestures=[g.gesture.value for g in intent.gestures],
            gaze_target=intent.gaze.target,
            dialogue_state="velaris",
            processing_time_ms=processing_time_ms,
        )

    await ws.send_text(make_status_message("ready").to_json())


# =============================================================================
# Standalone Mode Pipeline (Legacy Phase 1-5)
# =============================================================================

async def _handle_standalone_dialogue(ws: WebSocket, session: SessionState, user_text: str) -> None:
    """Standalone mode: Full Phase 1-5 pipeline with local LLM."""
    turn_start = time.time()
    session.conversation_turn += 1
    session.is_thinking = True

    log.info("Turn %d [Standalone]: user said: %s", session.conversation_turn, user_text[:100])

    # --- Memory & Context ---
    session.memory.add_turn("user", user_text)

    # --- Dialogue FSM ---
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

    if dialogue_state != prev_state:
        modifiers = {
            "gestureScale": session.dialogue_fsm.modifiers.gesture_scale,
            "distanceBias": session.dialogue_fsm.modifiers.distance_bias,
            "toneHint": session.dialogue_fsm.modifiers.tone_hint,
        }
        await ws.send_text(make_dialogue_state_message(dialogue_state.value, modifiers).to_json())

        if session.telemetry:
            session.telemetry.record_state_transition(prev_state.value, dialogue_state.value)

    # --- Build context-aware LLM prompt ---
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

    await ws.send_text(make_status_message("thinking").to_json())

    # --- Stream LLM response ---
    accumulated = ""
    early_intent_sent = False

    async for chunk in session.llm.chat_stream(user_text):
        accumulated += chunk

        if not early_intent_sent:
            early_intent = parse_streaming_chunk(accumulated)
            if early_intent:
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

    # Enrich with emotion analysis
    text_emotion = analyze_text(intent.speech_text)
    intent.emotion.valence = intent.emotion.valence * 0.7 + text_emotion.valence * 0.3
    intent.emotion.arousal = intent.emotion.arousal * 0.7 + text_emotion.arousal * 0.3

    # --- Emotional arc tracking ---
    arc = session.emotional_arc.record(intent.emotion, session.conversation_turn)
    arc_modifiers = session.emotional_arc.get_behavior_modifiers()

    await ws.send_text(make_arc_state_message(
        rapport=arc.rapport,
        valence_momentum=arc.valence_momentum,
        dominant_emotion=arc.dominant_emotion.value,
        is_recovering=arc.is_recovering,
    ).to_json())

    if session.telemetry:
        session.telemetry.record_rapport(arc.rapport)

    # --- Memory - record assistant turn ---
    session.memory.add_turn(
        "assistant",
        intent.speech_text,
        emotion_primary=intent.emotion.primary.value,
        emotion_valence=intent.emotion.valence,
        emotion_arousal=intent.emotion.arousal,
    )

    # --- Gesture selection ---
    personality_mods = session.personality.modifiers
    fsm_mods = session.dialogue_fsm.modifiers

    choreography_gestures = session.choreography.select_choreography(
        intent.emotion,
        intent.speech_text,
        dialogue_state=dialogue_state.value,
        rapport=arc.rapport,
    )

    if choreography_gestures and fsm_mods.use_choreography:
        intent.gestures = choreography_gestures
    else:
        intent.gestures = select_gestures(intent.emotion, intent.speech_text)

    gesture_scale = (
        personality_mods.gesture_amplitude
        * fsm_mods.gesture_scale
        * arc_modifiers["gesture_intensity"]
    )
    for g in intent.gestures:
        g.intensity = min(1.0, g.intensity * gesture_scale)

    # --- Micro-expressions ---
    basic_micros = select_micro_expressions(intent.emotion)
    advanced_micros = session.micro_engine.generate(
        current_emotion=intent.emotion,
        speech_text=intent.speech_text,
        user_text=user_text,
        turn_number=session.conversation_turn,
        rapport=arc.rapport,
    )

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
    intent.gaze.weight *= personality_mods.eye_contact_duration

    # --- Compute spatial positioning ---
    spatial = session.proximity_model.compute_spatial(
        intent.emotion,
        session.conversation_turn,
        session.user_anchor.state.body_position,
    )
    if spatial:
        spatial.target_distance += personality_mods.preferred_distance - 1.5
        spatial.target_distance += arc_modifiers.get("approach_bias", 0.0)
        spatial.target_distance += fsm_mods.distance_bias
        spatial.target_distance = max(settings.min_distance, min(settings.max_distance, spatial.target_distance))
        intent.spatial = spatial

    log.info(
        "Turn %d [Standalone]: state=%s emotion=%s (v=%.2f a=%.2f) rapport=%.2f gestures=%s gaze=%s",
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

    # --- TTS ---
    await _synthesize_and_send(ws, session, intent)

    # --- Telemetry ---
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

    await ws.send_text(make_status_message("ready").to_json())


# =============================================================================
# Shared helpers
# =============================================================================

async def _synthesize_and_send(ws: WebSocket, session: SessionState, intent: AvatarIntent) -> None:
    """Synthesize TTS and send audio + visemes to client."""
    if intent.speech_text and session.tts.enabled:
        session.is_speaking = True
        duration_est = session.tts.estimate_duration(intent.speech_text)

        await ws.send_text(make_speech_start_message(intent.speech_text, duration_est).to_json())

        visemes = generate_visemes(intent.speech_text, duration_est)
        if visemes:
            await ws.send_text(make_viseme_message(visemes).to_json())

        chunks = await session.tts.synthesize_streaming(intent.speech_text)
        for audio_b64, chunk_idx in chunks:
            await ws.send_text(
                make_speech_audio_message(audio_b64, session.tts.sample_rate, chunk_idx).to_json()
            )

        await ws.send_text(make_speech_end_message().to_json())
        session.is_speaking = False

    elif intent.speech_text:
        duration_est = session.tts.estimate_duration(intent.speech_text)
        await ws.send_text(make_speech_start_message(intent.speech_text, duration_est).to_json())

        visemes = generate_visemes(intent.speech_text, duration_est)
        if visemes:
            await ws.send_text(make_viseme_message(visemes).to_json())

        await ws.send_text(make_speech_end_message().to_json())


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
