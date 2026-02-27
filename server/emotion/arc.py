"""Emotional arc tracker — models how emotion evolves over the conversation.

Tracks:
  - Emotional momentum (trending happier, sadder, calmer, etc.)
  - Rapport level (0-1 scale of conversational connection)
  - Emotional volatility (how much emotion is fluctuating)
  - Recovery detection (detecting when negative emotion subsides)

Feeds into gesture/spatial/voice decisions for more coherent long-form behavior.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from server.intent.schema import Emotion, PrimaryEmotion


@dataclass
class EmotionSample:
    """A single emotion reading at a point in time."""
    valence: float
    arousal: float
    dominance: float
    primary: PrimaryEmotion
    timestamp: float = field(default_factory=time.time)
    turn_number: int = 0


@dataclass
class ArcState:
    """Current state of the emotional arc."""
    # Momentum: positive = trending happier, negative = trending sadder
    valence_momentum: float = 0.0
    arousal_momentum: float = 0.0

    # Rapport: 0 = stranger, 1 = deep connection
    rapport: float = 0.2

    # Volatility: 0 = stable, 1 = highly fluctuating
    volatility: float = 0.0

    # Dominant emotion over recent window
    dominant_emotion: PrimaryEmotion = PrimaryEmotion.NEUTRAL

    # Is the conversation in a recovery phase? (coming back from negative)
    is_recovering: bool = False

    # Average emotion over the session
    session_valence: float = 0.0
    session_arousal: float = 0.3


class EmotionalArcTracker:
    """Tracks the emotional trajectory of a conversation."""

    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size
        self.history: deque[EmotionSample] = deque(maxlen=100)
        self.state = ArcState()
        self._turn_count = 0

    def record(self, emotion: Emotion, turn_number: int) -> ArcState:
        """Record an emotion sample and return the updated arc state."""
        sample = EmotionSample(
            valence=emotion.valence,
            arousal=emotion.arousal,
            dominance=emotion.dominance,
            primary=emotion.primary,
            turn_number=turn_number,
        )
        self.history.append(sample)
        self._turn_count = turn_number

        self._update_momentum()
        self._update_rapport(emotion)
        self._update_volatility()
        self._update_dominant_emotion()
        self._update_session_averages()
        self._detect_recovery()

        return self.state

    def get_behavior_modifiers(self) -> dict[str, float]:
        """Get modifiers that influence avatar behavior based on arc state.

        Returns multipliers/offsets for various subsystems:
          - gesture_intensity: scale gesture expressiveness
          - spatial_comfort: adjust proxemic distance bias
          - gaze_intimacy: how much eye contact to maintain
          - voice_warmth: TTS tone modifier (future)
          - expression_depth: how pronounced facial expressions should be
        """
        s = self.state

        # High rapport = more expressive, closer, more eye contact
        rapport_factor = s.rapport

        # Recovery = gentler, more careful behavior
        recovery_dampen = 0.7 if s.is_recovering else 1.0

        # Volatile conversation = slightly muted reactions (don't amplify chaos)
        volatility_dampen = 1.0 - s.volatility * 0.3

        return {
            "gesture_intensity": (0.6 + rapport_factor * 0.4) * recovery_dampen * volatility_dampen,
            "spatial_comfort": rapport_factor,  # 0 = keep distance, 1 = close is ok
            "gaze_intimacy": 0.5 + rapport_factor * 0.4,  # baseline eye contact + rapport boost
            "expression_depth": (0.5 + rapport_factor * 0.5) * recovery_dampen,
            "approach_bias": -0.1 + rapport_factor * 0.2,  # meters: negative = farther, positive = closer
        }

    def _update_momentum(self) -> None:
        """Calculate emotional momentum from recent history."""
        if len(self.history) < 2:
            return

        recent = list(self.history)[-self.window_size:]
        if len(recent) < 2:
            return

        # Linear trend via first vs second half comparison
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]

        avg_v_first = sum(s.valence for s in first_half) / len(first_half)
        avg_v_second = sum(s.valence for s in second_half) / len(second_half)
        avg_a_first = sum(s.arousal for s in first_half) / len(first_half)
        avg_a_second = sum(s.arousal for s in second_half) / len(second_half)

        # Momentum: positive = trending up, range roughly -1 to 1
        self.state.valence_momentum = max(-1.0, min(1.0, (avg_v_second - avg_v_first) * 2.0))
        self.state.arousal_momentum = max(-1.0, min(1.0, (avg_a_second - avg_a_first) * 2.0))

    def _update_rapport(self, emotion: Emotion) -> None:
        """Update rapport level based on conversation flow."""
        # Rapport grows naturally with turns
        turn_growth = min(self._turn_count / 40.0, 0.5)  # caps at 0.5 from turns alone

        # Positive emotions boost rapport
        if emotion.valence > 0.2:
            emotion_boost = emotion.valence * 0.05
        elif emotion.valence < -0.3:
            # Negative emotions can still build rapport (emotional sharing)
            # but only if arousal is moderate (not pure anger)
            if emotion.arousal < 0.7:
                emotion_boost = 0.02
            else:
                emotion_boost = -0.02
        else:
            emotion_boost = 0.0

        # Momentum contributes: improving mood = rapport building
        momentum_boost = max(0, self.state.valence_momentum) * 0.03

        target_rapport = turn_growth + emotion_boost + momentum_boost + 0.2  # base 0.2
        target_rapport = max(0.0, min(1.0, target_rapport))

        # Smooth transition
        alpha = 0.15
        self.state.rapport = self.state.rapport * (1 - alpha) + target_rapport * alpha

    def _update_volatility(self) -> None:
        """Measure how much emotion is fluctuating."""
        recent = list(self.history)[-self.window_size:]
        if len(recent) < 3:
            self.state.volatility = 0.0
            return

        # Standard deviation of valence
        vals = [s.valence for s in recent]
        mean_v = sum(vals) / len(vals)
        variance = sum((v - mean_v) ** 2 for v in vals) / len(vals)
        std_v = variance ** 0.5

        # Map to 0-1 range (std of 0.5 ≈ maximum expected volatility)
        self.state.volatility = min(1.0, std_v / 0.5)

    def _update_dominant_emotion(self) -> None:
        """Find the most common emotion in the recent window."""
        recent = list(self.history)[-self.window_size:]
        if not recent:
            return

        counts: dict[PrimaryEmotion, int] = {}
        for sample in recent:
            counts[sample.primary] = counts.get(sample.primary, 0) + 1

        self.state.dominant_emotion = max(counts, key=counts.get)  # type: ignore[arg-type]

    def _update_session_averages(self) -> None:
        """Running averages over the full session."""
        if not self.history:
            return

        all_samples = list(self.history)
        self.state.session_valence = sum(s.valence for s in all_samples) / len(all_samples)
        self.state.session_arousal = sum(s.arousal for s in all_samples) / len(all_samples)

    def _detect_recovery(self) -> None:
        """Detect if we're recovering from a negative emotional episode."""
        recent = list(self.history)[-self.window_size:]
        if len(recent) < 4:
            self.state.is_recovering = False
            return

        # Recovery: earlier samples were negative, recent ones are trending positive
        first_quarter = recent[:len(recent) // 4]
        last_quarter = recent[-(len(recent) // 4):]

        early_valence = sum(s.valence for s in first_quarter) / len(first_quarter)
        late_valence = sum(s.valence for s in last_quarter) / len(last_quarter)

        self.state.is_recovering = early_valence < -0.2 and late_valence > early_valence + 0.15
