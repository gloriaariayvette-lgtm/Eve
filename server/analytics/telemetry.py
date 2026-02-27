"""Session analytics & behavior telemetry — tracks avatar behavior metrics.

Collects data about:
  - Emotion distribution over the session
  - Gesture usage frequency
  - Gaze pattern statistics
  - Spatial movement patterns
  - Dialogue state transitions
  - Turn timing and engagement metrics

Data is stored per-session and can be exported for analysis
to tune avatar behavior and personality parameters.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from server.intent.schema import Emotion, PrimaryEmotion

log = logging.getLogger(__name__)


@dataclass
class TurnMetrics:
    """Metrics for a single conversation turn."""
    turn_number: int
    timestamp: float
    user_text_length: int
    response_text_length: int
    emotion_primary: str
    emotion_valence: float
    emotion_arousal: float
    gestures_used: list[str]
    gaze_target: str
    dialogue_state: str
    processing_time_ms: float  # server-side processing time


@dataclass
class SessionMetrics:
    """Aggregated metrics for a complete session."""
    session_id: str
    start_time: float
    end_time: float = 0.0
    total_turns: int = 0
    total_user_words: int = 0
    total_response_words: int = 0

    # Emotion distribution
    emotion_counts: dict[str, int] = field(default_factory=dict)
    avg_valence: float = 0.0
    avg_arousal: float = 0.0
    valence_range: tuple[float, float] = (0.0, 0.0)

    # Gesture usage
    gesture_counts: dict[str, int] = field(default_factory=dict)
    total_gestures: int = 0

    # Gaze
    gaze_target_counts: dict[str, int] = field(default_factory=dict)

    # Dialogue states
    state_durations: dict[str, float] = field(default_factory=dict)
    state_transitions: int = 0

    # Performance
    avg_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0

    # Engagement
    peak_rapport: float = 0.0
    final_rapport: float = 0.0


class SessionTelemetry:
    """Collects and computes session analytics."""

    def __init__(self, session_id: str = "") -> None:
        self.session_id = session_id or f"session_{int(time.time())}"
        self.turn_log: list[TurnMetrics] = []
        self._start_time = time.time()
        self._valence_sum = 0.0
        self._arousal_sum = 0.0
        self._min_valence = 1.0
        self._max_valence = -1.0
        self._processing_times: list[float] = []
        self._state_enter_times: dict[str, float] = {}
        self._state_durations: dict[str, float] = {}
        self._state_transition_count = 0
        self._peak_rapport = 0.0

    def record_turn(
        self,
        turn_number: int,
        user_text: str,
        response_text: str,
        emotion: Emotion,
        gestures: list[str],
        gaze_target: str,
        dialogue_state: str,
        processing_time_ms: float,
    ) -> None:
        """Record metrics for a single turn."""
        metrics = TurnMetrics(
            turn_number=turn_number,
            timestamp=time.time(),
            user_text_length=len(user_text.split()),
            response_text_length=len(response_text.split()),
            emotion_primary=emotion.primary.value,
            emotion_valence=emotion.valence,
            emotion_arousal=emotion.arousal,
            gestures_used=gestures,
            gaze_target=gaze_target,
            dialogue_state=dialogue_state,
            processing_time_ms=processing_time_ms,
        )
        self.turn_log.append(metrics)

        # Running aggregates
        self._valence_sum += emotion.valence
        self._arousal_sum += emotion.arousal
        self._min_valence = min(self._min_valence, emotion.valence)
        self._max_valence = max(self._max_valence, emotion.valence)
        self._processing_times.append(processing_time_ms)

    def record_state_transition(self, old_state: str, new_state: str) -> None:
        """Record a dialogue state transition."""
        now = time.time()
        self._state_transition_count += 1

        # Accumulate time in old state
        if old_state in self._state_enter_times:
            duration = now - self._state_enter_times[old_state]
            self._state_durations[old_state] = self._state_durations.get(old_state, 0.0) + duration

        self._state_enter_times[new_state] = now

    def record_rapport(self, rapport: float) -> None:
        """Record current rapport level."""
        self._peak_rapport = max(self._peak_rapport, rapport)

    def compute_session_metrics(self, final_rapport: float = 0.0) -> SessionMetrics:
        """Compute final session metrics."""
        n = len(self.turn_log)
        if n == 0:
            return SessionMetrics(
                session_id=self.session_id,
                start_time=self._start_time,
                end_time=time.time(),
            )

        # Emotion distribution
        emotion_counts: dict[str, int] = {}
        gesture_counts: dict[str, int] = {}
        gaze_counts: dict[str, int] = {}
        total_user_words = 0
        total_response_words = 0
        total_gestures = 0

        for turn in self.turn_log:
            # Emotions
            emotion_counts[turn.emotion_primary] = emotion_counts.get(turn.emotion_primary, 0) + 1

            # Gestures
            for g in turn.gestures_used:
                gesture_counts[g] = gesture_counts.get(g, 0) + 1
                total_gestures += 1

            # Gaze
            gaze_counts[turn.gaze_target] = gaze_counts.get(turn.gaze_target, 0) + 1

            # Words
            total_user_words += turn.user_text_length
            total_response_words += turn.response_text_length

        return SessionMetrics(
            session_id=self.session_id,
            start_time=self._start_time,
            end_time=time.time(),
            total_turns=n,
            total_user_words=total_user_words,
            total_response_words=total_response_words,
            emotion_counts=emotion_counts,
            avg_valence=round(self._valence_sum / n, 3) if n > 0 else 0.0,
            avg_arousal=round(self._arousal_sum / n, 3) if n > 0 else 0.0,
            valence_range=(round(self._min_valence, 3), round(self._max_valence, 3)),
            gesture_counts=gesture_counts,
            total_gestures=total_gestures,
            gaze_target_counts=gaze_counts,
            state_durations={k: round(v, 1) for k, v in self._state_durations.items()},
            state_transitions=self._state_transition_count,
            avg_processing_time_ms=round(sum(self._processing_times) / len(self._processing_times), 1) if self._processing_times else 0.0,
            max_processing_time_ms=round(max(self._processing_times), 1) if self._processing_times else 0.0,
            peak_rapport=round(self._peak_rapport, 3),
            final_rapport=round(final_rapport, 3),
        )

    def export_json(self, path: str | None = None) -> str:
        """Export session metrics as JSON."""
        metrics = self.compute_session_metrics()
        data = {
            "session_id": metrics.session_id,
            "start_time": metrics.start_time,
            "end_time": metrics.end_time,
            "total_turns": metrics.total_turns,
            "total_user_words": metrics.total_user_words,
            "total_response_words": metrics.total_response_words,
            "emotion_counts": metrics.emotion_counts,
            "avg_valence": metrics.avg_valence,
            "avg_arousal": metrics.avg_arousal,
            "valence_range": list(metrics.valence_range),
            "gesture_counts": metrics.gesture_counts,
            "total_gestures": metrics.total_gestures,
            "gaze_target_counts": metrics.gaze_target_counts,
            "state_durations": metrics.state_durations,
            "state_transitions": metrics.state_transitions,
            "avg_processing_time_ms": metrics.avg_processing_time_ms,
            "max_processing_time_ms": metrics.max_processing_time_ms,
            "peak_rapport": metrics.peak_rapport,
            "final_rapport": metrics.final_rapport,
        }

        json_str = json.dumps(data, indent=2)

        if path:
            Path(path).write_text(json_str)
            log.info("Session telemetry exported to %s", path)

        return json_str
