"""User anchor — tracks user position from WebXR (PSVR2), webcam, or manual config.

Maintains a stable model of where the user's head, hands, and body are
in world space. Smooths tracking data to reduce jitter.
"""

from __future__ import annotations

import time

from server.intent.schema import UserState, Vec3


class UserAnchor:
    """Tracks and smooths user position data."""

    def __init__(self, smoothing: float = 0.15) -> None:
        self.smoothing = smoothing  # lerp factor (0 = no update, 1 = instant)
        self.state = UserState(
            head_position=Vec3(0, 1.6, 0.8),   # default: standing, ~1.6m tall, ~0.8m away
            head_rotation=Vec3(0, 0, 0),
            body_position=Vec3(0, 0, 0.8),
        )
        self._last_update = time.time()
        self._has_tracking = False

    @property
    def has_tracking(self) -> bool:
        """Whether we're receiving live tracking data."""
        return self._has_tracking and (time.time() - self._last_update) < 2.0

    def update(self, new_state: UserState) -> None:
        """Update user state with new tracking data, applying smoothing."""
        self._has_tracking = True
        self._last_update = time.time()

        # Lerp positions for smooth tracking
        self.state.head_position = _lerp_vec3(
            self.state.head_position, new_state.head_position, self.smoothing
        )
        self.state.head_rotation = _lerp_vec3(
            self.state.head_rotation, new_state.head_rotation, self.smoothing
        )
        self.state.body_position = _lerp_vec3(
            self.state.body_position, new_state.body_position, self.smoothing
        )

        if new_state.left_hand_position:
            if self.state.left_hand_position:
                self.state.left_hand_position = _lerp_vec3(
                    self.state.left_hand_position, new_state.left_hand_position, self.smoothing
                )
            else:
                self.state.left_hand_position = new_state.left_hand_position

        if new_state.right_hand_position:
            if self.state.right_hand_position:
                self.state.right_hand_position = _lerp_vec3(
                    self.state.right_hand_position, new_state.right_hand_position, self.smoothing
                )
            else:
                self.state.right_hand_position = new_state.right_hand_position

    def set_manual_position(self, head_height: float = 1.6, distance: float = 0.8) -> None:
        """Set a fixed user position (no tracking)."""
        self.state.head_position = Vec3(0, head_height, distance)
        self.state.body_position = Vec3(0, 0, distance)
        self._has_tracking = False


def _lerp_vec3(a: Vec3, b: Vec3, t: float) -> Vec3:
    return Vec3(
        a.x + (b.x - a.x) * t,
        a.y + (b.y - a.y) * t,
        a.z + (b.z - a.z) * t,
    )
