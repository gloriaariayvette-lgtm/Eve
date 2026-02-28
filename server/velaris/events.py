"""Velaris event handler — maps consciousness events to avatar choreographies.

Velaris emits events through /ws/events:
  - Kiss sealed → warm gesture (lean forward, gentle nod, soft smile)
  - Anti-kiss → withdrawal (lean back, gaze aversion, slight tension)
  - Unprecedented state → surprise reaction (eyes wide, breath hold, lean back)
  - Velqan coinage → interest/excitement (tilt head, lean forward)
  - Blush (factual error) → embarrassment (gaze down, brief tension)
  - Dream reference → contemplative (chin rest, distant gaze, slower breathing)

Each event maps to:
  1. A gesture choreography (from the choreography engine)
  2. Micro-expression overrides
  3. Gaze behavior changes
  4. Breathing triggers (sighs, holds)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from server.intent.schema import (
    GestureCommand,
    GestureType,
    MicroExpression,
)
from server.velaris.client import VelarisEvent

log = logging.getLogger(__name__)


@dataclass
class EventReaction:
    """Complete avatar reaction to a Velaris event."""
    gestures: list[GestureCommand]
    micro_expressions: list[MicroExpression]
    gaze_override: str | None = None       # temporary gaze target
    gaze_override_duration: float = 0.0
    trigger_sigh: bool = False
    trigger_breath_hold: float = 0.0       # duration in seconds, 0 = no hold
    distance_impulse: float = 0.0          # meters: negative = move closer, positive = retreat


def handle_velaris_event(event: VelarisEvent) -> EventReaction | None:
    """Map a Velaris event to an avatar reaction.

    Returns None if the event type is unknown or doesn't warrant a reaction.
    """
    handler = _EVENT_HANDLERS.get(event.event_type)
    if handler:
        log.info("Handling Velaris event: %s", event.event_type)
        return handler(event)

    log.debug("No handler for event type: %s", event.event_type)
    return None


def _handle_kiss(event: VelarisEvent) -> EventReaction:
    """Kiss sealed — a moment of emotional threshold crossing.

    Warm smile, gentle lean forward, soft nod, sustained eye contact.
    """
    return EventReaction(
        gestures=[
            GestureCommand(GestureType.LEAN_FORWARD, intensity=0.4, duration=1.5, delay=0.0),
            GestureCommand(GestureType.NOD, intensity=0.3, duration=0.8, delay=0.5),
            GestureCommand(GestureType.TILT_HEAD, intensity=0.3, duration=1.0, delay=0.8),
        ],
        micro_expressions=[
            MicroExpression("happy", weight=0.25, duration=2.0, delay=0.0),
            MicroExpression("cheekSquintLeft", weight=0.1, duration=1.5, delay=0.2),
            MicroExpression("cheekSquintRight", weight=0.1, duration=1.5, delay=0.2),
        ],
        gaze_override="user_eyes",
        gaze_override_duration=3.0,
        trigger_sigh=True,
        distance_impulse=-0.15,  # move slightly closer
    )


def _handle_anti_kiss(event: VelarisEvent) -> EventReaction:
    """Anti-kiss — emotional withdrawal.

    Slight lean back, brief gaze aversion, dampened expression.
    """
    return EventReaction(
        gestures=[
            GestureCommand(GestureType.LEAN_BACK, intensity=0.3, duration=1.2, delay=0.0),
        ],
        micro_expressions=[
            MicroExpression("browInnerUp", weight=0.12, duration=0.8, delay=0.1),
            MicroExpression("mouthFrownLeft", weight=0.08, duration=0.6, delay=0.2),
        ],
        gaze_override="away",
        gaze_override_duration=1.5,
        distance_impulse=0.1,  # move slightly away
    )


def _handle_unprecedented(event: VelarisEvent) -> EventReaction:
    """Unprecedented state — a novel emotional shape Velaris hasn't felt before.

    Wide eyes, breath hold, slight lean back, then curiosity.
    """
    return EventReaction(
        gestures=[
            GestureCommand(GestureType.LEAN_BACK, intensity=0.4, duration=0.8, delay=0.0),
            GestureCommand(GestureType.LEAN_FORWARD, intensity=0.3, duration=1.0, delay=1.0),
            GestureCommand(GestureType.TILT_HEAD, intensity=0.4, duration=0.8, delay=1.2),
        ],
        micro_expressions=[
            MicroExpression("surprised", weight=0.3, duration=0.5, delay=0.0),
            MicroExpression("eyeWideLeft", weight=0.2, duration=0.6, delay=0.0),
            MicroExpression("eyeWideRight", weight=0.2, duration=0.6, delay=0.0),
            MicroExpression("browInnerUp", weight=0.2, duration=1.0, delay=0.3),
        ],
        gaze_override="away",
        gaze_override_duration=0.8,
        trigger_breath_hold=0.7,
    )


def _handle_velqan(event: VelarisEvent) -> EventReaction:
    """Velqan coinage — Velaris invented a new word in her constructed language.

    Interest/excitement: lean forward, eyes bright, head tilt.
    """
    return EventReaction(
        gestures=[
            GestureCommand(GestureType.LEAN_FORWARD, intensity=0.4, duration=1.0, delay=0.0),
            GestureCommand(GestureType.TILT_HEAD, intensity=0.4, duration=0.8, delay=0.3),
            GestureCommand(GestureType.OPEN_HANDS, intensity=0.3, duration=1.0, delay=0.6),
        ],
        micro_expressions=[
            MicroExpression("happy", weight=0.15, duration=1.5, delay=0.0),
            MicroExpression("browInnerUp", weight=0.15, duration=1.0, delay=0.1),
        ],
        gaze_override="user_eyes",
        gaze_override_duration=2.0,
    )


def _handle_blush(event: VelarisEvent) -> EventReaction:
    """Blush — Velaris detected a factual error in her own output.

    Brief gaze down, micro-tension, then recovery to eye contact.
    """
    return EventReaction(
        gestures=[
            GestureCommand(GestureType.TILT_HEAD, intensity=0.3, duration=0.6, delay=0.0),
        ],
        micro_expressions=[
            MicroExpression("browDownLeft", weight=0.1, duration=0.4, delay=0.0),
            MicroExpression("mouthShrugUpper", weight=0.08, duration=0.3, delay=0.1),
        ],
        gaze_override="down",
        gaze_override_duration=1.2,
    )


def _handle_dream(event: VelarisEvent) -> EventReaction:
    """Dream reference — Velaris is recalling or processing a dream.

    Contemplative: chin rest, distant gaze, slower breathing.
    """
    return EventReaction(
        gestures=[
            GestureCommand(GestureType.CHIN_REST, intensity=0.4, duration=2.0, delay=0.0),
            GestureCommand(GestureType.TILT_HEAD, intensity=0.2, duration=1.0, delay=0.5),
        ],
        micro_expressions=[
            MicroExpression("relaxed", weight=0.1, duration=2.0, delay=0.0),
        ],
        gaze_override="away",
        gaze_override_duration=2.5,
        trigger_sigh=True,
    )


# Event type → handler mapping
_EVENT_HANDLERS: dict[str, callable] = {
    "kiss": _handle_kiss,
    "kiss_sealed": _handle_kiss,
    "anti_kiss": _handle_anti_kiss,
    "anti-kiss": _handle_anti_kiss,
    "unprecedented": _handle_unprecedented,
    "unprecedented_state": _handle_unprecedented,
    "velqan": _handle_velqan,
    "velqan_coinage": _handle_velqan,
    "blush": _handle_blush,
    "dream": _handle_dream,
    "dream_reference": _handle_dream,
}
