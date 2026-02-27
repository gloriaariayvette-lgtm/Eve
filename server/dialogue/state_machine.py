"""Dialogue state machine — models the conversational flow between avatar and user.

States represent the phase of interaction:
  - idle:         No active conversation, avatar in ambient mode
  - greeting:     Initial contact, establishing connection
  - small_talk:   Light conversation, building rapport
  - engaged:      Active, substantive conversation
  - emotional:    Deep emotional sharing or support
  - farewell:     Winding down, saying goodbye
  - listening:    Avatar is actively listening (user speaking at length)

Transitions are driven by:
  - User input content (greeting words, farewell words, emotional keywords)
  - Emotion state (high arousal → engaged, sadness → emotional)
  - Silence duration (long silence → idle)
  - Turn count (many turns → deeper states)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum

from server.intent.schema import Emotion, PrimaryEmotion

log = logging.getLogger(__name__)


class DialogueState(str, Enum):
    IDLE = "idle"
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    ENGAGED = "engaged"
    EMOTIONAL = "emotional"
    FAREWELL = "farewell"
    LISTENING = "listening"


@dataclass
class StateContext:
    """Contextual data used for state transitions."""
    user_text: str = ""
    emotion: Emotion = field(default_factory=Emotion)
    turn_count: int = 0
    silence_seconds: float = 0.0
    rapport: float = 0.2
    is_user_speaking: bool = False
    active_topics: list[str] = field(default_factory=list)


@dataclass
class StateModifiers:
    """Behavior modifiers applied based on current dialogue state."""
    # How much to scale gesture expressiveness
    gesture_scale: float = 1.0
    # Bias on proxemic distance (negative = closer)
    distance_bias: float = 0.0
    # Gaze behavior override
    preferred_gaze: str | None = None
    # Whether to use choreographed gestures vs single
    use_choreography: bool = False
    # Speaking rate modifier (1.0 = normal)
    speaking_rate: float = 1.0
    # Voice warmth / tone hint
    tone_hint: str = "neutral"


# State-specific behavior modifiers
_STATE_MODIFIERS: dict[DialogueState, StateModifiers] = {
    DialogueState.IDLE: StateModifiers(
        gesture_scale=0.3,
        distance_bias=0.3,
        preferred_gaze="away",
        tone_hint="quiet",
    ),
    DialogueState.GREETING: StateModifiers(
        gesture_scale=0.8,
        distance_bias=0.0,
        use_choreography=True,
        tone_hint="warm",
    ),
    DialogueState.SMALL_TALK: StateModifiers(
        gesture_scale=0.7,
        distance_bias=0.0,
        tone_hint="friendly",
    ),
    DialogueState.ENGAGED: StateModifiers(
        gesture_scale=1.0,
        distance_bias=-0.1,
        tone_hint="engaged",
    ),
    DialogueState.EMOTIONAL: StateModifiers(
        gesture_scale=0.6,
        distance_bias=-0.2,
        preferred_gaze="user_eyes",
        tone_hint="gentle",
        speaking_rate=0.9,
    ),
    DialogueState.FAREWELL: StateModifiers(
        gesture_scale=0.7,
        distance_bias=0.2,
        use_choreography=True,
        tone_hint="warm",
    ),
    DialogueState.LISTENING: StateModifiers(
        gesture_scale=0.4,
        preferred_gaze="user_eyes",
        tone_hint="attentive",
    ),
}


class DialogueStateMachine:
    """Manages dialogue state transitions and provides behavior modifiers."""

    def __init__(self) -> None:
        self.current_state = DialogueState.IDLE
        self.previous_state = DialogueState.IDLE
        self.state_entered_at = time.time()
        self.state_turn_count = 0
        self._transition_history: list[tuple[DialogueState, float]] = []

    @property
    def time_in_state(self) -> float:
        """Seconds spent in current state."""
        return time.time() - self.state_entered_at

    @property
    def modifiers(self) -> StateModifiers:
        """Get behavior modifiers for the current state."""
        return _STATE_MODIFIERS.get(self.current_state, StateModifiers())

    def update(self, context: StateContext) -> DialogueState:
        """Evaluate transitions and return the (possibly new) state."""
        new_state = self._evaluate_transitions(context)

        if new_state != self.current_state:
            log.info(
                "Dialogue state: %s → %s (turn %d)",
                self.current_state.value,
                new_state.value,
                context.turn_count,
            )
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_entered_at = time.time()
            self.state_turn_count = 0
            self._transition_history.append((new_state, time.time()))
        else:
            self.state_turn_count += 1

        return self.current_state

    def _evaluate_transitions(self, ctx: StateContext) -> DialogueState:
        """Determine what state we should be in."""
        text_lower = ctx.user_text.lower().strip()

        # --- Priority transitions (can happen from any state) ---

        # Farewell detection
        if self._is_farewell(text_lower):
            return DialogueState.FAREWELL

        # Long silence → idle
        if ctx.silence_seconds > 120 and self.current_state != DialogueState.IDLE:
            return DialogueState.IDLE

        # --- State-specific transitions ---

        if self.current_state == DialogueState.IDLE:
            if text_lower:
                if self._is_greeting(text_lower):
                    return DialogueState.GREETING
                return DialogueState.SMALL_TALK

        elif self.current_state == DialogueState.GREETING:
            # After greeting exchange, move to small talk
            if self.state_turn_count >= 1:
                if self._is_emotional_content(text_lower, ctx.emotion):
                    return DialogueState.EMOTIONAL
                return DialogueState.SMALL_TALK

        elif self.current_state == DialogueState.SMALL_TALK:
            if self._is_emotional_content(text_lower, ctx.emotion):
                return DialogueState.EMOTIONAL
            # Deepen to engaged after several turns or topic depth
            if ctx.turn_count >= 4 or ctx.rapport > 0.5:
                if len(ctx.active_topics) >= 2 or self.state_turn_count >= 3:
                    return DialogueState.ENGAGED

        elif self.current_state == DialogueState.ENGAGED:
            if self._is_emotional_content(text_lower, ctx.emotion):
                return DialogueState.EMOTIONAL
            # Can drop back to small talk after topic change
            if ctx.silence_seconds > 30:
                return DialogueState.SMALL_TALK

        elif self.current_state == DialogueState.EMOTIONAL:
            # Stay emotional if content is still heavy
            if self._is_emotional_content(text_lower, ctx.emotion):
                return DialogueState.EMOTIONAL
            # Recover to engaged after emotional content subsides
            if self.state_turn_count >= 3 and ctx.emotion.valence > 0:
                return DialogueState.ENGAGED
            if self.state_turn_count >= 5:
                return DialogueState.ENGAGED

        elif self.current_state == DialogueState.FAREWELL:
            # Farewell can bounce back if user continues talking
            if self.state_turn_count >= 2 and not self._is_farewell(text_lower):
                return DialogueState.SMALL_TALK

        elif self.current_state == DialogueState.LISTENING:
            # Return to previous conversational state when done
            if not ctx.is_user_speaking:
                return self.previous_state if self.previous_state != DialogueState.LISTENING else DialogueState.ENGAGED

        return self.current_state

    def _is_greeting(self, text: str) -> bool:
        greetings = ["hello", "hi ", "hi!", "hey", "good morning", "good afternoon",
                      "good evening", "howdy", "what's up", "sup", "yo "]
        return any(text.startswith(g) or text == g.strip() for g in greetings)

    def _is_farewell(self, text: str) -> bool:
        farewells = ["goodbye", "bye", "see you", "take care", "good night",
                     "goodnight", "gotta go", "have to go", "talk later",
                     "ttyl", "cya", "farewell"]
        return any(f in text for f in farewells)

    def _is_emotional_content(self, text: str, emotion: Emotion) -> bool:
        # High emotional intensity from the emotion model
        if abs(emotion.valence) > 0.5 and emotion.arousal > 0.5:
            return True

        # Emotional keywords
        emotional_words = [
            "feel", "feeling", "sad", "depressed", "anxious", "scared",
            "worried", "hurt", "painful", "crying", "cry", "lonely",
            "lost", "struggling", "overwhelmed", "stressed", "afraid",
            "heartbroken", "grieving", "miss you", "love you",
        ]
        return any(w in text for w in emotional_words)
