"""Proximity model — manages conversational distance and spatial behavior.

Based on Edward Hall's proxemic zones:
  - Intimate:  0.0 - 0.45m (reserved for close emotional moments)
  - Personal:  0.45 - 1.2m (friends, personal conversation)
  - Social:    1.2 - 3.6m (acquaintances, formal conversation)
  - Public:    3.6m+       (public speaking, presentations)

The avatar adjusts its distance based on emotion, conversation depth,
and user comfort signals.
"""

from __future__ import annotations

from server.config import settings
from server.intent.schema import Emotion, PrimaryEmotion, SpatialAction, SpatialCommand, Vec3


# Proxemic zone boundaries (meters)
INTIMATE_MAX = 0.45
PERSONAL_MAX = 1.2
SOCIAL_MAX = 3.6


class ProximityModel:
    def __init__(self) -> None:
        self.current_distance = settings.default_distance
        self.target_distance = settings.default_distance
        self.comfort_level = 0.5  # 0 = uncomfortable, 1 = very comfortable

    def compute_spatial(
        self,
        emotion: Emotion,
        conversation_turn: int,
        user_position: Vec3,
    ) -> SpatialCommand | None:
        """Compute spatial movement command based on emotion and context."""

        # Gradually decrease distance as conversation deepens (builds rapport)
        rapport_factor = min(conversation_turn / 20.0, 1.0)  # maxes out at 20 turns
        base_distance = settings.default_distance - rapport_factor * 0.3

        # Emotion-based distance adjustments
        emotion_offset = self._emotion_distance_offset(emotion)
        self.target_distance = max(
            settings.min_distance,
            min(settings.max_distance, base_distance + emotion_offset),
        )

        # Only emit a command if distance change is significant
        distance_delta = abs(self.target_distance - self.current_distance)
        if distance_delta < 0.1:
            return None

        # Determine action
        if self.target_distance < self.current_distance:
            action = SpatialAction.APPROACH
        else:
            action = SpatialAction.RETREAT

        # Movement speed based on arousal (excited = faster movement)
        speed = 0.3 + emotion.arousal * 0.4

        self.current_distance = self.target_distance

        return SpatialCommand(
            action=action,
            target_distance=round(self.target_distance, 2),
            speed=round(speed, 2),
        )

    def request_behavior(self, action: SpatialAction, speed: float = 0.5) -> SpatialCommand:
        """Explicitly request a spatial behavior (circle, sit, kneel, etc.)."""
        return SpatialCommand(
            action=action,
            target_distance=self.current_distance,
            speed=speed,
        )

    def _emotion_distance_offset(self, emotion: Emotion) -> float:
        """How much to adjust distance based on emotion."""
        offsets: dict[PrimaryEmotion, float] = {
            PrimaryEmotion.NEUTRAL:    0.0,
            PrimaryEmotion.JOY:        -0.15,   # move closer when happy
            PrimaryEmotion.TENDERNESS: -0.25,   # closer for warmth
            PrimaryEmotion.INTEREST:   -0.1,    # lean in
            PrimaryEmotion.SADNESS:    -0.1,    # gentle closeness for comfort
            PrimaryEmotion.ANGER:      0.2,     # back off
            PrimaryEmotion.FEAR:       0.3,     # retreat
            PrimaryEmotion.DISGUST:    0.2,     # back off
            PrimaryEmotion.SURPRISE:   0.1,     # slight retreat
            PrimaryEmotion.CONTEMPT:   0.15,    # slight distance
        }
        return offsets.get(emotion.primary, 0.0)
