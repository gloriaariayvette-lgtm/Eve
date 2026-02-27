"""WebSocket message protocol between server and client.

Message types flow in both directions:

Server → Client:
  - avatar_intent: Full avatar command frame (emotion, gesture, gaze, spatial)
  - speech_audio: Audio chunk for TTS playback
  - viseme_sequence: Timed visemes for lip sync
  - status: Connection/system status updates

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
    """Phase 4: Notify client of dialogue state transitions."""
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
    """Phase 4: Send emotional arc state to client for UI/debug."""
    return Message(type="arc_state", data={
        "rapport": round(rapport, 3),
        "valenceMomentum": round(valence_momentum, 3),
        "dominantEmotion": dominant_emotion,
        "isRecovering": is_recovering,
    })


def make_session_metrics_message(metrics: dict) -> Message:
    """Phase 5: Send session analytics snapshot."""
    return Message(type="session_metrics", data=metrics)


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
