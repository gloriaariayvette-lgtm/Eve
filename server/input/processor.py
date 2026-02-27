"""Multi-modal input processor — aggregates signals beyond text for avatar behavior.

Processes and normalizes multiple input channels:
  - Text input (primary, from user typed messages)
  - Voice activity events (user starts/stops speaking — for active listening)
  - Proximity events (user moves closer/farther)
  - Attention events (user looks at/away from avatar)
  - Gesture events (user hand gestures detected via tracking)

Outputs a unified input context that the dialogue pipeline can use
to adjust avatar behavior even between explicit text messages.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger(__name__)


class InputChannel(str, Enum):
    TEXT = "text"
    VOICE_ACTIVITY = "voice_activity"
    PROXIMITY = "proximity"
    ATTENTION = "attention"
    GESTURE = "gesture"


@dataclass
class InputEvent:
    """A discrete input event from any channel."""
    channel: InputChannel
    event_type: str      # channel-specific event name
    value: float = 0.0   # numeric value (meaning depends on channel)
    data: dict = field(default_factory=dict)  # extra data
    timestamp: float = field(default_factory=time.time)


@dataclass
class InputContext:
    """Aggregated input state across all channels."""
    # Voice
    user_is_speaking: bool = False
    voice_activity_duration: float = 0.0   # seconds of current speech
    last_voice_end: float = 0.0

    # Proximity
    user_distance: float = 1.5             # meters from avatar
    distance_trend: float = 0.0            # positive = moving away, negative = approaching
    is_approaching: bool = False
    is_retreating: bool = False

    # Attention
    user_looking_at_avatar: bool = True
    attention_duration: float = 0.0        # seconds of continuous attention
    attention_ratio: float = 1.0           # fraction of recent time looking at avatar

    # Gestures
    user_gesturing: bool = False
    last_gesture_type: str = ""

    # Engagement score: 0 (disengaged) to 1 (fully engaged)
    engagement_score: float = 0.5

    # Whether to trigger idle behaviors (long silence, no input)
    should_idle: bool = False

    # Whether the avatar should react (significant input event)
    should_react: bool = False
    reaction_type: str = ""   # "user_approaching", "user_looked_away", "user_started_speaking", etc.


class InputProcessor:
    """Processes multi-modal input into a unified context."""

    def __init__(self) -> None:
        self.context = InputContext()
        self._voice_start_time: float = 0
        self._attention_start_time: float = time.time()
        self._last_distance: float = 1.5
        self._attention_history: list[bool] = []  # recent attention samples
        self._max_attention_samples = 60  # ~1 second at 60fps
        self._last_event_time: float = time.time()
        self._idle_threshold: float = 60.0  # seconds before idle triggers

    def process_event(self, event: InputEvent) -> InputContext:
        """Process an input event and update the context."""
        self._last_event_time = time.time()
        self.context.should_react = False
        self.context.reaction_type = ""

        if event.channel == InputChannel.VOICE_ACTIVITY:
            self._handle_voice(event)
        elif event.channel == InputChannel.PROXIMITY:
            self._handle_proximity(event)
        elif event.channel == InputChannel.ATTENTION:
            self._handle_attention(event)
        elif event.channel == InputChannel.GESTURE:
            self._handle_gesture(event)

        self._update_engagement()
        return self.context

    def update(self, dt: float) -> InputContext:
        """Periodic update — call every frame or at regular intervals."""
        now = time.time()

        # Voice duration tracking
        if self.context.user_is_speaking:
            self.context.voice_activity_duration = now - self._voice_start_time

        # Attention duration tracking
        if self.context.user_looking_at_avatar:
            self.context.attention_duration = now - self._attention_start_time
        else:
            self.context.attention_duration = 0

        # Distance trend decay
        self.context.distance_trend *= 0.95  # decay toward 0

        # Idle detection
        idle_duration = now - self._last_event_time
        self.context.should_idle = idle_duration > self._idle_threshold

        self._update_engagement()
        return self.context

    def _handle_voice(self, event: InputEvent) -> None:
        if event.event_type == "start":
            if not self.context.user_is_speaking:
                self.context.user_is_speaking = True
                self._voice_start_time = time.time()
                self.context.should_react = True
                self.context.reaction_type = "user_started_speaking"
                log.debug("Voice activity: user started speaking")

        elif event.event_type == "stop":
            if self.context.user_is_speaking:
                self.context.user_is_speaking = False
                self.context.last_voice_end = time.time()
                self.context.voice_activity_duration = 0
                log.debug("Voice activity: user stopped speaking")

    def _handle_proximity(self, event: InputEvent) -> None:
        new_distance = event.value
        delta = new_distance - self._last_distance

        self.context.distance_trend = delta
        self.context.user_distance = new_distance

        # Detect approach/retreat
        approach_threshold = -0.1  # 10cm closer
        retreat_threshold = 0.1    # 10cm farther

        if delta < approach_threshold:
            if not self.context.is_approaching:
                self.context.is_approaching = True
                self.context.is_retreating = False
                self.context.should_react = True
                self.context.reaction_type = "user_approaching"
        elif delta > retreat_threshold:
            if not self.context.is_retreating:
                self.context.is_retreating = True
                self.context.is_approaching = False
                self.context.should_react = True
                self.context.reaction_type = "user_retreating"
        else:
            self.context.is_approaching = False
            self.context.is_retreating = False

        self._last_distance = new_distance

    def _handle_attention(self, event: InputEvent) -> None:
        looking = event.event_type == "looking_at"

        if looking and not self.context.user_looking_at_avatar:
            self._attention_start_time = time.time()
            self.context.should_react = True
            self.context.reaction_type = "user_looked_at"

        if not looking and self.context.user_looking_at_avatar:
            self.context.should_react = True
            self.context.reaction_type = "user_looked_away"

        self.context.user_looking_at_avatar = looking

        # Update attention ratio
        self._attention_history.append(looking)
        if len(self._attention_history) > self._max_attention_samples:
            self._attention_history.pop(0)

        if self._attention_history:
            self.context.attention_ratio = sum(self._attention_history) / len(self._attention_history)

    def _handle_gesture(self, event: InputEvent) -> None:
        self.context.user_gesturing = event.event_type != "none"
        self.context.last_gesture_type = event.event_type
        if event.event_type != "none":
            self.context.should_react = True
            self.context.reaction_type = f"user_gesture_{event.event_type}"

    def _update_engagement(self) -> None:
        """Compute engagement score from all input signals."""
        ctx = self.context

        # Factors that increase engagement
        score = 0.3  # base

        if ctx.user_looking_at_avatar:
            score += 0.25 * ctx.attention_ratio

        if ctx.user_is_speaking:
            score += 0.2

        if ctx.is_approaching:
            score += 0.1

        if ctx.user_gesturing:
            score += 0.1

        # Factors that decrease engagement
        if not ctx.user_looking_at_avatar and ctx.attention_ratio < 0.3:
            score -= 0.2

        if ctx.is_retreating:
            score -= 0.1

        ctx.engagement_score = max(0.0, min(1.0, score))
