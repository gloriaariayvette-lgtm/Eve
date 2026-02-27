"""Gaze model — decides where the avatar should look.

Uses conversation context, emotion, and user tracking data to produce
natural gaze behavior: maintain eye contact, glance at hands during
gestures, look away when thinking, micro-saccades for liveness.
"""

from __future__ import annotations

import random
import time

from server.intent.schema import Emotion, GazeTarget, PrimaryEmotion, UserState, Vec3


class GazeModel:
    def __init__(self) -> None:
        self._last_saccade = time.time()
        self._saccade_interval = 0.3  # seconds between micro-saccades
        self._last_look_away = time.time()
        self._look_away_duration = 0.0
        self._is_looking_away = False

    def compute_gaze(
        self,
        emotion: Emotion,
        user_state: UserState,
        is_speaking: bool,
        is_thinking: bool,
    ) -> GazeTarget:
        """Compute gaze target based on current state."""
        now = time.time()

        # When thinking (waiting for LLM), look away naturally
        if is_thinking:
            if not self._is_looking_away:
                self._is_looking_away = True
                self._last_look_away = now
                self._look_away_duration = random.uniform(0.5, 2.0)

            if now - self._last_look_away < self._look_away_duration:
                direction = random.choice(["away", "down"])
                return GazeTarget(
                    target=direction,
                    weight=0.6,
                    offset=Vec3(
                        random.uniform(-0.3, 0.3),
                        random.uniform(-0.2, 0.1),
                        0.0,
                    ),
                )
            else:
                self._is_looking_away = False

        # Default: look at user's eyes
        target = "user_eyes"
        weight = 0.9

        # Emotion-based gaze adjustments
        if emotion.primary == PrimaryEmotion.SADNESS:
            # Sad → occasional downward glances
            if random.random() < 0.3:
                target = "down"
                weight = 0.5
        elif emotion.primary == PrimaryEmotion.FEAR:
            # Fearful → break eye contact more often
            if random.random() < 0.4:
                target = "away"
                weight = 0.4
        elif emotion.primary == PrimaryEmotion.INTEREST:
            # Interested → strong eye contact, lean in
            weight = 1.0
        elif emotion.primary == PrimaryEmotion.CONTEMPT:
            # Contempt → slightly averted gaze
            weight = 0.6

        # If user has hand tracking, occasionally glance at hands during emphasis
        if user_state.left_hand_position or user_state.right_hand_position:
            if is_speaking and random.random() < 0.1:
                target = "user_hands"
                weight = 0.4

        # Micro-saccade offset for liveness
        saccade_offset = Vec3()
        if now - self._last_saccade > self._saccade_interval:
            saccade_offset = Vec3(
                random.gauss(0, 0.02),
                random.gauss(0, 0.01),
                0.0,
            )
            self._last_saccade = now
            self._saccade_interval = random.uniform(0.2, 0.5)

        return GazeTarget(target=target, weight=weight, offset=saccade_offset)
