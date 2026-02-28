"""Intent router — builds AvatarIntent from Velaris emotional state + response text.

Phase 4-5 (standalone) used LLM [EMOTION][GESTURE][GAZE] tags parsed by regex.
Velaris integration replaces this: emotion comes from EmoClaw (11-dimensional,
measured, reliable), gestures/gaze are derived by the avatar's own systems.

This module now provides two paths:
  1. from_velaris_state() — primary path, uses EmoClaw state + plain text
  2. parse_llm_response() — legacy fallback for standalone mode with tag parsing
"""

from __future__ import annotations

import logging
import re

from server.intent.schema import (
    AvatarIntent,
    Emotion,
    GazeTarget,
    GestureCommand,
    GestureType,
    PrimaryEmotion,
)

log = logging.getLogger(__name__)


def from_velaris_state(
    speech_text: str,
    emotion: Emotion,
) -> AvatarIntent:
    """Build an AvatarIntent from Velaris's EmoClaw state + response text.

    This is the primary path for Velaris integration. Emotion comes from
    the EmoClaw bridge (11-dim → VAD + primary), speech text is Velaris's
    plain response. Gestures and gaze are left empty — they'll be filled
    by the gesture engine and gaze model downstream in the pipeline.
    """
    return AvatarIntent(
        speech_text=speech_text.strip(),
        emotion=emotion,
        gestures=[],     # filled by gesture engine / choreography
        gaze=GazeTarget(),  # filled by gaze model
    )


# ---- Legacy standalone mode (LLM tag parsing) ----

# Pattern: [EMOTION: joy | INTENSITY: 0.8]
_EMOTION_RE = re.compile(
    r"\[EMOTION:\s*(\w+)\s*\|\s*INTENSITY:\s*([\d.]+)\]",
    re.IGNORECASE,
)
# Pattern: [GESTURE: nod]
_GESTURE_RE = re.compile(r"\[GESTURE:\s*(\w+)\]", re.IGNORECASE)
# Pattern: [GAZE: user_eyes]
_GAZE_RE = re.compile(r"\[GAZE:\s*(\w+)\]", re.IGNORECASE)


# Emotion → VAD (valence, arousal, dominance) mapping
_EMOTION_VAD: dict[PrimaryEmotion, tuple[float, float, float]] = {
    PrimaryEmotion.NEUTRAL:    (0.0,  0.2, 0.5),
    PrimaryEmotion.JOY:        (0.8,  0.6, 0.6),
    PrimaryEmotion.SADNESS:    (-0.7, 0.3, 0.2),
    PrimaryEmotion.ANGER:      (-0.6, 0.8, 0.8),
    PrimaryEmotion.SURPRISE:   (0.2,  0.8, 0.4),
    PrimaryEmotion.FEAR:       (-0.7, 0.7, 0.2),
    PrimaryEmotion.DISGUST:    (-0.6, 0.5, 0.6),
    PrimaryEmotion.CONTEMPT:   (-0.4, 0.4, 0.7),
    PrimaryEmotion.INTEREST:   (0.4,  0.5, 0.5),
    PrimaryEmotion.TENDERNESS: (0.7,  0.3, 0.4),
}


def parse_llm_response(raw_text: str) -> AvatarIntent:
    """Legacy: Parse a complete LLM response with [EMOTION][GESTURE][GAZE] tags."""
    primary, intensity = _parse_emotion_tag(raw_text)
    gesture_type = _parse_gesture_tag(raw_text)
    gaze_target = _parse_gaze_tag(raw_text)
    speech_text = _strip_tags(raw_text)

    base_v, base_a, base_d = _EMOTION_VAD.get(primary, (0.0, 0.2, 0.5))
    emotion = Emotion(
        valence=base_v * intensity,
        arousal=base_a + (1.0 - base_a) * intensity * 0.5,
        dominance=base_d,
        primary=primary,
    )

    gestures: list[GestureCommand] = []
    if gesture_type != GestureType.NONE:
        gestures.append(GestureCommand(
            gesture=gesture_type,
            intensity=intensity,
            duration=1.0 + intensity * 0.5,
        ))

    valid_targets = {"user_eyes", "user_hands", "user_body", "away", "down", "object"}
    if gaze_target not in valid_targets:
        gaze_target = "user_eyes"
    gaze = GazeTarget(target=gaze_target, weight=0.8 + intensity * 0.2)

    return AvatarIntent(
        speech_text=speech_text,
        emotion=emotion,
        gestures=gestures,
        gaze=gaze,
    )


def parse_streaming_chunk(accumulated_text: str) -> AvatarIntent | None:
    """Legacy: Try to parse a partial response as it streams in."""
    if not _EMOTION_RE.search(accumulated_text):
        return None
    return parse_llm_response(accumulated_text)


def _parse_emotion_tag(text: str) -> tuple[PrimaryEmotion, float]:
    match = _EMOTION_RE.search(text)
    if not match:
        return PrimaryEmotion.NEUTRAL, 0.3
    name = match.group(1).lower()
    intensity = max(0.0, min(1.0, float(match.group(2))))
    try:
        primary = PrimaryEmotion(name)
    except ValueError:
        primary = PrimaryEmotion.NEUTRAL
    return primary, intensity


def _parse_gesture_tag(text: str) -> GestureType:
    match = _GESTURE_RE.search(text)
    if not match:
        return GestureType.NONE
    try:
        return GestureType(match.group(1).lower())
    except ValueError:
        return GestureType.NONE


def _parse_gaze_tag(text: str) -> str:
    match = _GAZE_RE.search(text)
    if not match:
        return "user_eyes"
    return match.group(1).lower()


def _strip_tags(text: str) -> str:
    cleaned = re.sub(r"\[(?:EMOTION|GESTURE|GAZE):[^\]]*\]", "", text)
    return cleaned.strip()
