"""Advanced micro-expression engine — procedural facial reactions with emotional leakage.

Goes beyond the basic emotion → blend shape mapping to produce:
  - Emotional leakage: suppressed emotions bleeding through briefly
  - Reactive flashes: brief facial reactions to user input keywords
  - Asymmetric expressions: one-sided smirks, single brow raises
  - Conversational backchannel: subtle nodding/expression during user speech
  - Emotional blending: e.g., bittersweet = sad + slight smile

Each micro-expression has:
  - onset time (when it starts)
  - apex time (peak intensity)
  - offset time (when it fades)
  - asymmetry factor (how one-sided it is)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from server.intent.schema import Emotion, MicroExpression, PrimaryEmotion


@dataclass
class MicroExpressionConfig:
    """Configuration for a single micro-expression type."""
    blend_shape: str
    max_weight: float
    onset_duration: float   # seconds to reach peak
    apex_duration: float    # seconds at peak
    offset_duration: float  # seconds to fade
    asymmetry: float = 0.0  # 0 = symmetric, >0 = right side stronger, <0 = left


# Emotional leakage: brief flashes of suppressed emotion
_LEAKAGE_EXPRESSIONS: dict[PrimaryEmotion, list[MicroExpressionConfig]] = {
    PrimaryEmotion.JOY: [
        MicroExpressionConfig("mouthSmileLeft", 0.15, 0.05, 0.1, 0.15, asymmetry=-0.3),
        MicroExpressionConfig("cheekSquintLeft", 0.1, 0.05, 0.08, 0.1),
    ],
    PrimaryEmotion.SADNESS: [
        MicroExpressionConfig("browInnerUp", 0.2, 0.06, 0.12, 0.2),
        MicroExpressionConfig("mouthFrownLeft", 0.1, 0.05, 0.08, 0.15, asymmetry=-0.2),
    ],
    PrimaryEmotion.ANGER: [
        MicroExpressionConfig("browDownLeft", 0.15, 0.04, 0.06, 0.1),
        MicroExpressionConfig("jawForward", 0.08, 0.05, 0.08, 0.12),
    ],
    PrimaryEmotion.FEAR: [
        MicroExpressionConfig("eyeWideLeft", 0.12, 0.03, 0.05, 0.1),
        MicroExpressionConfig("browInnerUp", 0.18, 0.04, 0.06, 0.12),
    ],
    PrimaryEmotion.SURPRISE: [
        MicroExpressionConfig("eyeWideLeft", 0.2, 0.03, 0.08, 0.15),
        MicroExpressionConfig("eyeWideRight", 0.2, 0.03, 0.08, 0.15),
        MicroExpressionConfig("browOuterUpLeft", 0.15, 0.04, 0.1, 0.12),
    ],
    PrimaryEmotion.CONTEMPT: [
        MicroExpressionConfig("mouthSmileRight", 0.12, 0.06, 0.15, 0.2, asymmetry=0.4),
    ],
    PrimaryEmotion.DISGUST: [
        MicroExpressionConfig("noseSneerLeft", 0.15, 0.04, 0.08, 0.12),
        MicroExpressionConfig("mouthShrugUpper", 0.08, 0.05, 0.1, 0.15),
    ],
}

# Reactive micro-expressions triggered by keywords in user speech
_REACTIVE_TRIGGERS: list[tuple[list[str], list[MicroExpressionConfig]]] = [
    # Compliment → brief genuine smile
    (
        ["beautiful", "amazing", "wonderful", "great job", "love it", "brilliant"],
        [
            MicroExpressionConfig("happy", 0.2, 0.1, 0.3, 0.2),
            MicroExpressionConfig("browInnerUp", 0.1, 0.05, 0.15, 0.1),
        ],
    ),
    # Bad news → empathetic frown
    (
        ["died", "cancer", "accident", "terrible", "horrible", "devastating"],
        [
            MicroExpressionConfig("sad", 0.15, 0.08, 0.2, 0.3),
            MicroExpressionConfig("browInnerUp", 0.2, 0.06, 0.15, 0.2),
        ],
    ),
    # Confusion → brow scrunch
    (
        ["confused", "don't understand", "makes no sense", "what do you mean"],
        [
            MicroExpressionConfig("browDownLeft", 0.12, 0.05, 0.15, 0.15),
            MicroExpressionConfig("browDownRight", 0.12, 0.05, 0.15, 0.15),
        ],
    ),
    # Humor → Duchenne smile markers
    (
        ["haha", "lol", "funny", "hilarious", "joke", "lmao"],
        [
            MicroExpressionConfig("happy", 0.25, 0.08, 0.3, 0.2),
            MicroExpressionConfig("cheekSquintLeft", 0.15, 0.1, 0.2, 0.15),
            MicroExpressionConfig("cheekSquintRight", 0.15, 0.1, 0.2, 0.15),
        ],
    ),
]


class AdvancedMicroExpressionEngine:
    """Generates nuanced micro-expressions for avatar facial animation."""

    def __init__(self) -> None:
        self._last_leakage_turn: int = 0
        self._suppressed_emotion: PrimaryEmotion | None = None

    def generate(
        self,
        current_emotion: Emotion,
        speech_text: str,
        user_text: str,
        turn_number: int,
        rapport: float = 0.5,
    ) -> list[MicroExpression]:
        """Generate micro-expressions for a turn.

        Combines:
          1. Primary emotion expressions (from gesture engine — already handled)
          2. Emotional leakage (new)
          3. Reactive expressions to user content (new)
          4. Conversational blend expressions (new)
        """
        micros: list[MicroExpression] = []

        # 1. Emotional leakage — if the primary emotion changed recently,
        #    occasionally flash the previous emotion
        leakage = self._generate_leakage(current_emotion, turn_number)
        micros.extend(leakage)

        # 2. Reactive expressions to user speech content
        reactive = self._generate_reactive(user_text, rapport)
        micros.extend(reactive)

        # 3. Emotional blend expressions (e.g., bittersweet)
        blended = self._generate_blended(current_emotion)
        micros.extend(blended)

        return micros

    def _generate_leakage(
        self,
        current_emotion: Emotion,
        turn_number: int,
    ) -> list[MicroExpression]:
        """Occasionally leak the suppressed previous emotion."""
        # Track emotion transitions
        if self._suppressed_emotion and self._suppressed_emotion != current_emotion.primary:
            # The old emotion was replaced — it might leak
            if turn_number - self._last_leakage_turn >= 2 and random.random() < 0.3:
                self._last_leakage_turn = turn_number
                configs = _LEAKAGE_EXPRESSIONS.get(self._suppressed_emotion, [])
                if configs:
                    config = random.choice(configs)
                    delay = random.uniform(0.5, 2.0)
                    return [MicroExpression(
                        blend_shape=config.blend_shape,
                        weight=config.max_weight * 0.6,  # leakage is subtle
                        duration=config.onset_duration + config.apex_duration + config.offset_duration,
                        delay=delay,
                    )]

        self._suppressed_emotion = current_emotion.primary
        return []

    def _generate_reactive(self, user_text: str, rapport: float) -> list[MicroExpression]:
        """Generate micro-expressions in reaction to user speech content."""
        if not user_text:
            return []

        text_lower = user_text.lower()
        micros: list[MicroExpression] = []

        for keywords, configs in _REACTIVE_TRIGGERS:
            if any(kw in text_lower for kw in keywords):
                # Pick 1-2 expressions from the triggered set
                selected = random.sample(configs, min(2, len(configs)))
                for config in selected:
                    # Scale by rapport — more responsive when connected
                    weight = config.max_weight * (0.5 + rapport * 0.5)
                    delay = random.uniform(0.1, 0.5)
                    micros.append(MicroExpression(
                        blend_shape=config.blend_shape,
                        weight=round(weight, 3),
                        duration=config.onset_duration + config.apex_duration + config.offset_duration,
                        delay=delay,
                    ))
                break  # only trigger one reactive set per turn

        return micros

    def _generate_blended(self, emotion: Emotion) -> list[MicroExpression]:
        """Generate blended expressions for complex emotional states."""
        micros: list[MicroExpression] = []

        # Bittersweet: negative valence but with slight smile
        if -0.4 < emotion.valence < 0 and emotion.primary == PrimaryEmotion.SADNESS:
            if random.random() < 0.4:
                micros.append(MicroExpression(
                    blend_shape="mouthSmileLeft",
                    weight=0.08,
                    duration=0.6,
                    delay=random.uniform(0.3, 1.0),
                ))

        # Nervous excitement: high arousal + slight fear/joy mix
        if emotion.arousal > 0.7 and emotion.primary == PrimaryEmotion.JOY:
            if random.random() < 0.3:
                micros.append(MicroExpression(
                    blend_shape="browInnerUp",
                    weight=0.12,
                    duration=0.4,
                    delay=random.uniform(0.2, 0.8),
                ))

        # Skeptical interest: interest + slight brow down
        if emotion.primary == PrimaryEmotion.INTEREST and emotion.dominance > 0.6:
            if random.random() < 0.3:
                micros.append(MicroExpression(
                    blend_shape="browDownRight",
                    weight=0.1,
                    duration=0.5,
                    delay=random.uniform(0.2, 0.6),
                ))

        return micros
