"""WebSocket message protocol between server and client.

Message types flow in both directions:

Server → Client:
  - avatar_intent: Full avatar command frame (emotion, gesture, gaze, spatial)
  - speech_audio: Audio chunk for TTS playback
  - viseme_sequence: Timed visemes for lip sync
  - status: Connection/system status updates
  - dialogue_state: Dialogue FSM state transitions (standalone mode)
  - arc_state: Emotional arc state (rapport, momentum)
  - session_metrics: Session analytics snapshot
  - emotional_color: Velaris emotional color for environment lighting
  - behavior_modifiers: EmoClaw-derived behavior modifiers
  - velaris_event: Velaris event reaction (kiss, anti-kiss, etc.)

Client → Server:
  - user_input: Text input from the user
  - user_tracking: Head/hand tracking data from WebXR/PSVR2
  - config: Runtime configuration changes
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from server.intent.schema import AvatarIntent, UserState, Viseme


@dataclass
class Message:
    """Base WebSocket message."""
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_json(cls, raw: str) -> Message:
        obj = json.loads(raw)
        return cls(
            type=obj["type"],
            data=obj.get("data", {}),
            timestamp=obj.get("timestamp", time.time()),
        )


# --- Server → Client messages ---

def make_intent_message(intent: AvatarIntent) -> Message:
    return Message(type="avatar_intent", data=intent.to_dict())


def make_speech_start_message(text: str, duration_estimate: float) -> Message:
    return Message(type="speech_start", data={
        "text": text,
        "durationEstimate": duration_estimate,
    })


def make_speech_audio_message(audio_b64: str, sample_rate: int, chunk_index: int) -> Message:
    return Message(type="speech_audio", data={
        "audio": audio_b64,
        "sampleRate": sample_rate,
        "chunkIndex": chunk_index,
    })


def make_speech_end_message() -> Message:
    return Message(type="speech_end", data={})


def make_viseme_message(visemes: list[Viseme]) -> Message:
    return Message(type="viseme_sequence", data={
        "visemes": [v.to_dict() for v in visemes],
    })


def make_status_message(status: str, detail: str = "") -> Message:
    return Message(type="status", data={"status": status, "detail": detail})


def make_dialogue_state_message(state: str, modifiers: dict | None = None) -> Message:
    """Notify client of dialogue state transitions."""
    data: dict = {"state": state}
    if modifiers:
        data["modifiers"] = modifiers
    return Message(type="dialogue_state", data=data)


def make_arc_state_message(
    rapport: float,
    valence_momentum: float,
    dominant_emotion: str,
    is_recovering: bool,
) -> Message:
    """Send emotional arc state to client for UI/debug."""
    return Message(type="arc_state", data={
        "rapport": round(rapport, 3),
        "valenceMomentum": round(valence_momentum, 3),
        "dominantEmotion": dominant_emotion,
        "isRecovering": is_recovering,
    })


def make_session_metrics_message(metrics: dict) -> Message:
    """Send session analytics snapshot."""
    return Message(type="session_metrics", data=metrics)


def make_emotional_color_message(color: str) -> Message:
    """Velaris: Send emotional color for environment lighting."""
    return Message(type="emotional_color", data={
        "color": color,
    })


def make_behavior_modifiers_message(modifiers: Any) -> Message:
    """Velaris: Send EmoClaw-derived behavior modifiers to client."""
    return Message(type="behavior_modifiers", data={
        "gestureFrequency": modifiers.gesture_frequency,
        "gestureAmplitude": modifiers.gesture_amplitude,
        "gesturePlayfulness": modifiers.gesture_playfulness,
        "preferredDistance": modifiers.preferred_distance,
        "approachWillingness": modifiers.approach_willingness,
        "shouldLeanForward": modifiers.should_lean_forward,
        "postureStability": modifiers.posture_stability,
        "eyeContactIntensity": modifiers.eye_contact_intensity,
        "gazeCuriosity": modifiers.gaze_curiosity,
        "gazeWarmth": modifiers.gaze_warmth,
        "expressionDepth": modifiers.expression_depth,
        "warmthOverlay": modifiers.warmth_overlay,
        "tensionOverlay": modifiers.tension_overlay,
        "breathRateModifier": modifiers.breath_rate_modifier,
        "breathDepthModifier": modifiers.breath_depth_modifier,
        "emotionalColor": modifiers.emotional_color,
    })


def make_velaris_event_message(
    event_type: str,
    gestures: list[dict],
    micro_expressions: list[dict],
    gaze_override: str | None = None,
    gaze_override_duration: float = 0.0,
    trigger_sigh: bool = False,
    trigger_breath_hold: float = 0.0,
    distance_impulse: float = 0.0,
) -> Message:
    """Velaris: Send event reaction to client (kiss, anti-kiss, unprecedented, etc.)."""
    return Message(type="velaris_event", data={
        "eventType": event_type,
        "gestures": gestures,
        "microExpressions": micro_expressions,
        "gazeOverride": gaze_override,
        "gazeOverrideDuration": gaze_override_duration,
        "triggerSigh": trigger_sigh,
        "triggerBreathHold": trigger_breath_hold,
        "distanceImpulse": distance_impulse,
    })


# --- Client → Server messages ---

def parse_user_input(msg: Message) -> str:
    return msg.data.get("text", "")


def parse_user_tracking(msg: Message) -> UserState:
    d = msg.data
    state = UserState()
    if "headPosition" in d:
        hp = d["headPosition"]
        from server.intent.schema import Vec3
        state.head_position = Vec3(hp.get("x", 0), hp.get("y", 0), hp.get("z", 0))
    if "headRotation" in d:
        hr = d["headRotation"]
        from server.intent.schema import Vec3
        state.head_rotation = Vec3(hr.get("x", 0), hr.get("y", 0), hr.get("z", 0))
    if "leftHandPosition" in d:
        lh = d["leftHandPosition"]
        from server.intent.schema import Vec3
        state.left_hand_position = Vec3(lh.get("x", 0), lh.get("y", 0), lh.get("z", 0))
    if "rightHandPosition" in d:
        rh = d["rightHandPosition"]
        from server.intent.schema import Vec3
        state.right_hand_position = Vec3(rh.get("x", 0), rh.get("y", 0), rh.get("z", 0))
    return state
