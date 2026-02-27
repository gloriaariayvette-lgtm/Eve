"""Gesture choreography engine — multi-gesture sequences with coordinated timing.

Instead of single isolated gestures, this system produces choreographed
sequences that feel natural and contextual:
  - Greeting: wave → tilt_head → open_hands
  - Empathy: tilt_head → lean_forward → nod
  - Thinking: chin_rest → look away → nod (when done thinking)
  - Excitement: lean_forward → open_hands → nod
  - Farewell: nod → wave → lean_back

Sequences are selected based on dialogue state, emotion, and conversation context.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from server.intent.schema import Emotion, GestureCommand, GestureType, PrimaryEmotion


@dataclass
class ChoreographyStep:
    """A single step in a gesture sequence."""
    gesture: GestureType
    intensity: float
    duration: float
    delay: float  # delay from sequence start


@dataclass
class GestureSequence:
    """A named sequence of choreographed gestures."""
    name: str
    steps: list[ChoreographyStep]
    total_duration: float = 0.0

    def __post_init__(self) -> None:
        if self.steps:
            self.total_duration = max(s.delay + s.duration for s in self.steps)

    def to_commands(self, intensity_scale: float = 1.0) -> list[GestureCommand]:
        """Convert to a list of GestureCommands ready for the pipeline."""
        return [
            GestureCommand(
                gesture=step.gesture,
                intensity=min(1.0, step.intensity * intensity_scale),
                duration=step.duration,
                delay=step.delay,
            )
            for step in self.steps
        ]


# --- Pre-defined choreographies ---

_GREETING_SEQUENCES = [
    GestureSequence("warm_greeting", [
        ChoreographyStep(GestureType.WAVE, 0.6, 0.8, 0.0),
        ChoreographyStep(GestureType.TILT_HEAD, 0.4, 0.6, 0.5),
        ChoreographyStep(GestureType.OPEN_HANDS, 0.5, 1.0, 1.0),
    ]),
    GestureSequence("casual_greeting", [
        ChoreographyStep(GestureType.WAVE, 0.4, 0.6, 0.0),
        ChoreographyStep(GestureType.NOD, 0.5, 0.5, 0.4),
    ]),
]

_FAREWELL_SEQUENCES = [
    GestureSequence("warm_farewell", [
        ChoreographyStep(GestureType.NOD, 0.5, 0.6, 0.0),
        ChoreographyStep(GestureType.WAVE, 0.6, 1.0, 0.4),
        ChoreographyStep(GestureType.LEAN_BACK, 0.3, 0.8, 1.0),
    ]),
    GestureSequence("brief_farewell", [
        ChoreographyStep(GestureType.WAVE, 0.5, 0.8, 0.0),
        ChoreographyStep(GestureType.NOD, 0.4, 0.5, 0.5),
    ]),
]

_EMPATHY_SEQUENCES = [
    GestureSequence("deep_empathy", [
        ChoreographyStep(GestureType.TILT_HEAD, 0.5, 0.8, 0.0),
        ChoreographyStep(GestureType.LEAN_FORWARD, 0.4, 1.2, 0.3),
        ChoreographyStep(GestureType.NOD, 0.3, 0.6, 1.0),
    ]),
    GestureSequence("gentle_empathy", [
        ChoreographyStep(GestureType.TILT_HEAD, 0.4, 1.0, 0.0),
        ChoreographyStep(GestureType.NOD, 0.3, 0.5, 0.8),
    ]),
]

_EXCITEMENT_SEQUENCES = [
    GestureSequence("enthusiastic", [
        ChoreographyStep(GestureType.LEAN_FORWARD, 0.5, 0.6, 0.0),
        ChoreographyStep(GestureType.OPEN_HANDS, 0.7, 0.8, 0.3),
        ChoreographyStep(GestureType.NOD, 0.6, 0.5, 0.8),
    ]),
]

_THINKING_SEQUENCES = [
    GestureSequence("contemplation", [
        ChoreographyStep(GestureType.CHIN_REST, 0.5, 1.5, 0.0),
        ChoreographyStep(GestureType.TILT_HEAD, 0.3, 0.8, 1.0),
    ]),
    GestureSequence("pondering", [
        ChoreographyStep(GestureType.TILT_HEAD, 0.4, 0.8, 0.0),
        ChoreographyStep(GestureType.CHIN_REST, 0.4, 1.2, 0.5),
        ChoreographyStep(GestureType.NOD, 0.3, 0.5, 1.5),
    ]),
]

_AGREEMENT_SEQUENCES = [
    GestureSequence("strong_agreement", [
        ChoreographyStep(GestureType.NOD, 0.6, 0.5, 0.0),
        ChoreographyStep(GestureType.LEAN_FORWARD, 0.3, 0.6, 0.3),
        ChoreographyStep(GestureType.OPEN_HANDS, 0.4, 0.8, 0.6),
    ]),
]

_DISAGREEMENT_SEQUENCES = [
    GestureSequence("gentle_disagreement", [
        ChoreographyStep(GestureType.SHAKE_HEAD, 0.4, 0.6, 0.0),
        ChoreographyStep(GestureType.TILT_HEAD, 0.3, 0.5, 0.4),
        ChoreographyStep(GestureType.OPEN_HANDS, 0.3, 0.8, 0.7),
    ]),
]

_UNCERTAINTY_SEQUENCES = [
    GestureSequence("unsure", [
        ChoreographyStep(GestureType.TILT_HEAD, 0.4, 0.6, 0.0),
        ChoreographyStep(GestureType.SHRUG, 0.5, 0.8, 0.4),
    ]),
]

# Map from context tag → available sequences
_CONTEXT_CHOREOGRAPHIES: dict[str, list[GestureSequence]] = {
    "greeting": _GREETING_SEQUENCES,
    "farewell": _FAREWELL_SEQUENCES,
    "empathy": _EMPATHY_SEQUENCES,
    "excitement": _EXCITEMENT_SEQUENCES,
    "thinking": _THINKING_SEQUENCES,
    "agreement": _AGREEMENT_SEQUENCES,
    "disagreement": _DISAGREEMENT_SEQUENCES,
    "uncertainty": _UNCERTAINTY_SEQUENCES,
}


class ChoreographyEngine:
    """Selects and produces multi-gesture choreographies."""

    def __init__(self) -> None:
        self._last_choreography: str = ""
        self._cooldown_turns: int = 0

    def select_choreography(
        self,
        emotion: Emotion,
        speech_text: str,
        dialogue_state: str = "conversation",
        rapport: float = 0.5,
    ) -> list[GestureCommand] | None:
        """Select a choreography based on context. Returns None if no special
        choreography is warranted (fall back to single gesture selection)."""

        # Cooldown: don't fire choreographies every turn
        if self._cooldown_turns > 0:
            self._cooldown_turns -= 1
            return None

        context = self._detect_context(emotion, speech_text, dialogue_state)
        if not context:
            return None

        sequences = _CONTEXT_CHOREOGRAPHIES.get(context, [])
        if not sequences:
            return None

        # Pick one, avoiding immediate repeats
        candidates = [s for s in sequences if s.name != self._last_choreography]
        if not candidates:
            candidates = sequences

        sequence = random.choice(candidates)
        self._last_choreography = sequence.name
        self._cooldown_turns = 2  # skip 2 turns before next choreography

        # Scale intensity by rapport (higher rapport = more expressive)
        intensity_scale = 0.6 + rapport * 0.4

        return sequence.to_commands(intensity_scale)

    def _detect_context(
        self,
        emotion: Emotion,
        speech_text: str,
        dialogue_state: str,
    ) -> str | None:
        """Detect what choreography context applies."""
        text_lower = speech_text.lower()

        # Dialogue state overrides
        if dialogue_state == "greeting":
            return "greeting"
        if dialogue_state == "farewell":
            return "farewell"

        # Content-based detection
        if any(w in text_lower for w in ["hello", "hi ", "hey ", "good morning", "good evening", "welcome"]):
            return "greeting"
        if any(w in text_lower for w in ["goodbye", "bye", "see you", "take care", "goodnight"]):
            return "farewell"

        # Emotion-based detection
        if emotion.primary in (PrimaryEmotion.SADNESS, PrimaryEmotion.FEAR):
            if any(w in text_lower for w in ["sorry", "understand", "here for", "it's okay", "that's tough"]):
                return "empathy"

        if emotion.primary == PrimaryEmotion.JOY and emotion.arousal > 0.6:
            return "excitement"

        if any(w in text_lower for w in ["i think", "let me think", "hmm", "consider", "perhaps"]):
            return "thinking"

        if any(w in text_lower for w in ["absolutely", "exactly", "i agree", "definitely", "right"]):
            return "agreement"

        if any(w in text_lower for w in ["i disagree", "not quite", "actually", "however", "but i think"]):
            return "disagreement"

        if any(w in text_lower for w in ["not sure", "maybe", "i don't know", "hard to say"]):
            return "uncertainty"

        return None
