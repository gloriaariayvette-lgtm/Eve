"""Gesture engine — maps emotion + intent to body animation commands.

Selects contextually appropriate gestures based on:
- Current emotion (VAD model)
- Speech content (keywords/patterns)
- Conversation flow (is this a response, question, agreement?)
"""

from __future__ import annotations

import random

from server.intent.schema import (
    Emotion,
    GestureCommand,
    GestureType,
    MicroExpression,
    PrimaryEmotion,
)

# Emotion → likely gestures with base weights
_EMOTION_GESTURE_MAP: dict[PrimaryEmotion, list[tuple[GestureType, float]]] = {
    PrimaryEmotion.NEUTRAL:    [(GestureType.NONE, 0.6), (GestureType.TILT_HEAD, 0.2), (GestureType.NOD, 0.2)],
    PrimaryEmotion.JOY:        [(GestureType.NOD, 0.3), (GestureType.OPEN_HANDS, 0.3), (GestureType.LEAN_FORWARD, 0.2), (GestureType.WAVE, 0.2)],
    PrimaryEmotion.SADNESS:    [(GestureType.LEAN_BACK, 0.3), (GestureType.TILT_HEAD, 0.3), (GestureType.NONE, 0.4)],
    PrimaryEmotion.ANGER:      [(GestureType.ARMS_CROSSED, 0.3), (GestureType.LEAN_FORWARD, 0.3), (GestureType.SHAKE_HEAD, 0.2), (GestureType.POINT, 0.2)],
    PrimaryEmotion.SURPRISE:   [(GestureType.LEAN_BACK, 0.3), (GestureType.OPEN_HANDS, 0.4), (GestureType.TILT_HEAD, 0.3)],
    PrimaryEmotion.FEAR:       [(GestureType.LEAN_BACK, 0.4), (GestureType.ARMS_CROSSED, 0.3), (GestureType.NONE, 0.3)],
    PrimaryEmotion.DISGUST:    [(GestureType.LEAN_BACK, 0.4), (GestureType.SHAKE_HEAD, 0.3), (GestureType.NONE, 0.3)],
    PrimaryEmotion.CONTEMPT:   [(GestureType.ARMS_CROSSED, 0.3), (GestureType.TILT_HEAD, 0.3), (GestureType.LEAN_BACK, 0.2), (GestureType.NONE, 0.2)],
    PrimaryEmotion.INTEREST:   [(GestureType.LEAN_FORWARD, 0.4), (GestureType.TILT_HEAD, 0.3), (GestureType.CHIN_REST, 0.3)],
    PrimaryEmotion.TENDERNESS: [(GestureType.TILT_HEAD, 0.3), (GestureType.NOD, 0.3), (GestureType.LEAN_FORWARD, 0.2), (GestureType.OPEN_HANDS, 0.2)],
}

# Emotion → micro-expression blend shapes
_EMOTION_MICRO_EXPRESSIONS: dict[PrimaryEmotion, list[tuple[str, float, float]]] = {
    # (blend_shape_name, max_weight, duration)
    PrimaryEmotion.JOY:        [("happy", 0.3, 0.4), ("browInnerUp", 0.15, 0.3)],
    PrimaryEmotion.SADNESS:    [("sad", 0.25, 0.5), ("browInnerUp", 0.2, 0.4)],
    PrimaryEmotion.ANGER:      [("angry", 0.2, 0.3), ("browDownLeft", 0.15, 0.3), ("browDownRight", 0.15, 0.3)],
    PrimaryEmotion.SURPRISE:   [("surprised", 0.3, 0.2), ("browInnerUp", 0.3, 0.2)],
    PrimaryEmotion.FEAR:       [("browInnerUp", 0.25, 0.3), ("mouthOpen", 0.1, 0.2)],
    PrimaryEmotion.DISGUST:    [("noseSneerLeft", 0.2, 0.3), ("noseSneerRight", 0.2, 0.3)],
    PrimaryEmotion.CONTEMPT:   [("mouthSmileLeft", 0.15, 0.4)],
    PrimaryEmotion.INTEREST:   [("browInnerUp", 0.1, 0.3)],
    PrimaryEmotion.TENDERNESS: [("happy", 0.15, 0.5), ("browInnerUp", 0.1, 0.4)],
    PrimaryEmotion.NEUTRAL:    [],
}


def select_gestures(emotion: Emotion, speech_text: str) -> list[GestureCommand]:
    """Select appropriate gestures based on emotion and speech content."""
    gestures: list[GestureCommand] = []
    text_lower = speech_text.lower()

    # Content-based gesture overrides
    if any(w in text_lower for w in ["yes", "agree", "right", "exactly", "sure"]):
        gestures.append(GestureCommand(
            gesture=GestureType.NOD,
            intensity=0.5 + emotion.arousal * 0.3,
            duration=0.8,
        ))
        return gestures

    if any(w in text_lower for w in ["no", "disagree", "don't", "wrong", "never"]):
        gestures.append(GestureCommand(
            gesture=GestureType.SHAKE_HEAD,
            intensity=0.4 + emotion.arousal * 0.3,
            duration=0.8,
        ))
        return gestures

    if any(w in text_lower for w in ["don't know", "not sure", "maybe", "perhaps", "uncertain"]):
        gestures.append(GestureCommand(
            gesture=GestureType.SHRUG,
            intensity=0.5,
            duration=1.0,
        ))
        return gestures

    if any(w in text_lower for w in ["look", "see", "there", "this", "that"]):
        gestures.append(GestureCommand(
            gesture=GestureType.POINT,
            intensity=0.4,
            duration=1.2,
        ))

    # Emotion-based gesture selection (weighted random)
    options = _EMOTION_GESTURE_MAP.get(emotion.primary, [(GestureType.NONE, 1.0)])
    gesture_types = [g for g, _ in options]
    weights = [w for _, w in options]

    selected = random.choices(gesture_types, weights=weights, k=1)[0]
    if selected != GestureType.NONE:
        gestures.append(GestureCommand(
            gesture=selected,
            intensity=emotion.arousal * 0.7 + 0.3,
            duration=1.0 + (1.0 - emotion.arousal) * 0.5,
        ))

    return gestures


def select_micro_expressions(emotion: Emotion) -> list[MicroExpression]:
    """Select subtle facial micro-expressions based on emotion."""
    micros: list[MicroExpression] = []

    expressions = _EMOTION_MICRO_EXPRESSIONS.get(emotion.primary, [])
    for blend_shape, max_weight, duration in expressions:
        # Scale by arousal — more intense emotion = more visible micro-expressions
        weight = max_weight * (0.3 + emotion.arousal * 0.7)
        micros.append(MicroExpression(
            blend_shape=blend_shape,
            weight=round(weight, 3),
            duration=duration,
            delay=random.uniform(0.0, 0.3),
        ))

    return micros
