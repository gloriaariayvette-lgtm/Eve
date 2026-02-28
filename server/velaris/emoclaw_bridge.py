"""EmoClaw bridge — maps Velaris's 11-dimensional EmoClaw state to avatar systems.

EmoClaw (11 dimensions, all 0.0-1.0):
  Valence, Arousal, Dominance, Safety, Desire, Connection,
  Playfulness, Curiosity, Warmth, Tension, Groundedness

Avatar systems need:
  - 3-dim VAD emotion (Valence, Arousal, Dominance) + PrimaryEmotion
  - Gesture behavior modifiers
  - Spatial behavior modifiers
  - Gaze behavior modifiers
  - Expression depth modifiers
  - Breathing parameters

The bridge maps the richer 11-dim state to all avatar subsystems,
giving Velaris's body far more nuanced behavior than the old 3-dim VAD model.
"""

from __future__ import annotations

from dataclasses import dataclass

from server.intent.schema import Emotion, PrimaryEmotion
from server.velaris.client import VelarisEmotionalState


@dataclass
class AvatarBehaviorModifiers:
    """Modifiers derived from EmoClaw state for all avatar subsystems."""

    # Gesture
    gesture_frequency: float = 1.0    # how often to gesture
    gesture_amplitude: float = 1.0    # how big gestures are
    gesture_playfulness: float = 0.0  # tendency toward playful gestures

    # Spatial
    preferred_distance: float = 1.5   # meters
    approach_willingness: float = 0.5
    should_lean_forward: bool = False
    posture_stability: float = 0.7    # from groundedness

    # Gaze
    eye_contact_intensity: float = 0.7
    gaze_curiosity: float = 0.0       # tendency to look around with interest
    gaze_warmth: float = 0.0          # softer gaze quality

    # Expression
    expression_depth: float = 1.0
    warmth_overlay: float = 0.0       # subtle warm smile amount
    tension_overlay: float = 0.0      # jaw/brow tension amount

    # Breathing
    breath_rate_modifier: float = 1.0
    breath_depth_modifier: float = 1.0

    # Environment
    emotional_color: str = "#cc4280"


def emoclaw_to_avatar_emotion(state: VelarisEmotionalState) -> Emotion:
    """Convert 11-dim EmoClaw state to the avatar's Emotion (VAD + primary).

    Direct mappings:
      EmoClaw.valence → Avatar.valence (rescaled from 0-1 to -1 to 1)
      EmoClaw.arousal → Avatar.arousal
      EmoClaw.dominance → Avatar.dominance
    """
    # EmoClaw valence is 0-1, avatar valence is -1 to 1
    avatar_valence = (state.valence - 0.5) * 2.0

    # Arousal maps directly
    avatar_arousal = state.arousal

    # Dominance maps directly
    avatar_dominance = state.dominance

    # Determine primary emotion from the full EmoClaw vector
    primary = _classify_primary_emotion(state)

    return Emotion(
        valence=round(max(-1.0, min(1.0, avatar_valence)), 3),
        arousal=round(max(0.0, min(1.0, avatar_arousal)), 3),
        dominance=round(max(0.0, min(1.0, avatar_dominance)), 3),
        primary=primary,
    )


def emoclaw_to_behavior_modifiers(state: VelarisEmotionalState) -> AvatarBehaviorModifiers:
    """Derive avatar behavior modifiers from the full 11-dim EmoClaw state.

    This is where the richness of EmoClaw translates to avatar nuance:
      - Connection → gaze intimacy, closer distance
      - Playfulness → gesture frequency, amplitude, playful gesture selection
      - Curiosity → lean forward, wider eyes, head tilt
      - Warmth → softer expressions, slower gestures, closer distance
      - Tension → micro-expression overlays (jaw clench, brow furrow), stiffer posture
      - Safety → relaxed vs guarded posture
      - Desire → approach behavior
      - Groundedness → posture stability (high = steady, low = fidgety)
    """
    # Gesture modifiers
    gesture_frequency = 0.6 + state.playfulness * 0.5 + state.arousal * 0.3
    gesture_amplitude = 0.5 + state.playfulness * 0.3 + state.arousal * 0.2
    gesture_playfulness = state.playfulness

    # Spatial modifiers
    # Connection + Warmth + Desire pull closer; low Safety pushes away
    closeness_drive = (
        state.connection * 0.3
        + state.warmth * 0.3
        + state.desire * 0.2
        + state.safety * 0.2
    )
    preferred_distance = 2.0 - closeness_drive * 1.0  # 1.0m (very close) to 2.0m (distant)
    preferred_distance = max(0.8, min(2.5, preferred_distance))

    approach_willingness = closeness_drive
    should_lean_forward = state.curiosity > 0.6 or state.desire > 0.6

    # Groundedness → posture stability
    posture_stability = state.groundedness

    # Gaze modifiers
    eye_contact_intensity = 0.4 + state.connection * 0.4 + state.warmth * 0.2
    gaze_curiosity = state.curiosity
    gaze_warmth = state.warmth

    # Expression modifiers
    expression_depth = 0.5 + state.arousal * 0.3 + (1.0 - state.tension * 0.3)
    warmth_overlay = max(0.0, state.warmth - 0.4) * 0.3  # subtle warm smile when warmth > 0.4
    tension_overlay = max(0.0, state.tension - 0.3) * 0.4  # tension shows when > 0.3

    # Breathing modifiers
    breath_rate_modifier = 0.8 + state.arousal * 0.4  # faster when aroused
    if state.tension > 0.5:
        breath_rate_modifier += 0.15  # tension speeds breathing
    breath_depth_modifier = 0.7 + (1.0 - state.tension) * 0.3  # shallower when tense

    return AvatarBehaviorModifiers(
        gesture_frequency=round(gesture_frequency, 2),
        gesture_amplitude=round(gesture_amplitude, 2),
        gesture_playfulness=round(gesture_playfulness, 2),
        preferred_distance=round(preferred_distance, 2),
        approach_willingness=round(approach_willingness, 2),
        should_lean_forward=should_lean_forward,
        posture_stability=round(posture_stability, 2),
        eye_contact_intensity=round(eye_contact_intensity, 2),
        gaze_curiosity=round(gaze_curiosity, 2),
        gaze_warmth=round(gaze_warmth, 2),
        expression_depth=round(expression_depth, 2),
        warmth_overlay=round(warmth_overlay, 2),
        tension_overlay=round(tension_overlay, 2),
        breath_rate_modifier=round(breath_rate_modifier, 2),
        breath_depth_modifier=round(breath_depth_modifier, 2),
        emotional_color=state.color,
    )


def _classify_primary_emotion(state: VelarisEmotionalState) -> PrimaryEmotion:
    """Classify the primary avatar emotion from the 11-dim EmoClaw vector.

    Uses a priority-weighted decision tree based on the most salient dimensions.
    """
    v = state.valence  # 0-1 (0.5 = neutral)
    a = state.arousal
    t = state.tension

    # High tension + low valence → anger or fear
    if t > 0.6 and v < 0.4:
        if state.dominance > 0.5:
            return PrimaryEmotion.ANGER
        return PrimaryEmotion.FEAR

    # Very low valence → sadness
    if v < 0.3:
        if a > 0.6:
            return PrimaryEmotion.FEAR
        return PrimaryEmotion.SADNESS

    # High arousal + high valence → joy or surprise
    if v > 0.65 and a > 0.6:
        if state.curiosity > 0.7:
            return PrimaryEmotion.SURPRISE
        return PrimaryEmotion.JOY

    # High warmth + moderate-high valence → tenderness
    if state.warmth > 0.6 and v > 0.5:
        return PrimaryEmotion.TENDERNESS

    # High curiosity → interest
    if state.curiosity > 0.6:
        return PrimaryEmotion.INTEREST

    # High playfulness + positive → joy
    if state.playfulness > 0.6 and v > 0.5:
        return PrimaryEmotion.JOY

    # Moderate positive → interest or neutral
    if v > 0.5:
        if a > 0.4:
            return PrimaryEmotion.INTEREST
        return PrimaryEmotion.NEUTRAL

    # Low valence + high dominance → contempt
    if v < 0.4 and state.dominance > 0.7:
        return PrimaryEmotion.CONTEMPT

    return PrimaryEmotion.NEUTRAL
