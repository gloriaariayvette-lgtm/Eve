"""Core data types for the avatar motion engine pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class PrimaryEmotion(str, Enum):
    NEUTRAL = "neutral"
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    SURPRISE = "surprise"
    FEAR = "fear"
    DISGUST = "disgust"
    CONTEMPT = "contempt"
    INTEREST = "interest"
    TENDERNESS = "tenderness"


class GestureType(str, Enum):
    NONE = "none"
    NOD = "nod"
    SHAKE_HEAD = "shake_head"
    SHRUG = "shrug"
    LEAN_FORWARD = "lean_forward"
    LEAN_BACK = "lean_back"
    TILT_HEAD = "tilt_head"
    OPEN_HANDS = "open_hands"
    POINT = "point"
    WAVE = "wave"
    CHIN_REST = "chin_rest"
    ARMS_CROSSED = "arms_crossed"


class SpatialAction(str, Enum):
    HOLD = "hold"
    APPROACH = "approach"
    RETREAT = "retreat"
    CIRCLE = "circle"
    SIT = "sit"
    STAND = "stand"
    KNEEL = "kneel"
    MIRROR = "mirror"


class VisemeShape(str, Enum):
    SILENT = "silent"
    PP = "PP"    # p, b, m
    FF = "FF"    # f, v
    TH = "TH"    # th
    DD = "DD"    # t, d, n, l
    KK = "KK"    # k, g, ng
    CH = "CH"    # ch, j, sh, zh
    SS = "SS"    # s, z
    NN = "NN"    # n (nasal)
    RR = "RR"    # r
    AA = "AA"    # a (open)
    EE = "EE"    # e, i (spread)
    IH = "IH"    # i (short)
    OH = "OH"    # o (round)
    OO = "OO"    # u, oo (tight round)


@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class Emotion:
    """Valence-Arousal-Dominance emotion model."""
    valence: float = 0.0      # -1 (negative) to 1 (positive)
    arousal: float = 0.3      # 0 (calm) to 1 (excited)
    dominance: float = 0.5    # 0 (submissive) to 1 (dominant)
    primary: PrimaryEmotion = PrimaryEmotion.NEUTRAL

    def to_dict(self) -> dict:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "primary": self.primary.value,
        }


@dataclass
class GazeTarget:
    """Where the avatar should look."""
    target: Literal["user_eyes", "user_hands", "user_body", "away", "down", "object"] = "user_eyes"
    weight: float = 1.0       # 0-1 how strongly to look
    offset: Vec3 = field(default_factory=Vec3)

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "weight": self.weight,
            "offset": self.offset.to_dict(),
        }


@dataclass
class GestureCommand:
    """A body gesture to perform."""
    gesture: GestureType = GestureType.NONE
    intensity: float = 0.5    # 0-1
    duration: float = 1.0     # seconds
    delay: float = 0.0        # seconds before starting

    def to_dict(self) -> dict:
        return {
            "gesture": self.gesture.value,
            "intensity": self.intensity,
            "duration": self.duration,
            "delay": self.delay,
        }


@dataclass
class SpatialCommand:
    """Movement/positioning command."""
    action: SpatialAction = SpatialAction.HOLD
    target_distance: float = 1.5  # meters
    speed: float = 0.5            # m/s
    target_position: Vec3 | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "action": self.action.value,
            "targetDistance": self.target_distance,
            "speed": self.speed,
        }
        if self.target_position:
            d["targetPosition"] = self.target_position.to_dict()
        return d


@dataclass
class Viseme:
    """A single viseme for lip sync."""
    shape: VisemeShape = VisemeShape.SILENT
    weight: float = 0.0
    timestamp: float = 0.0    # seconds from utterance start

    def to_dict(self) -> dict:
        return {
            "shape": self.shape.value,
            "weight": self.weight,
            "timestamp": self.timestamp,
        }


@dataclass
class MicroExpression:
    """Subtle facial movement overlay."""
    blend_shape: str = ""     # VRM blend shape name
    weight: float = 0.0       # 0-1
    duration: float = 0.3     # seconds
    delay: float = 0.0

    def to_dict(self) -> dict:
        return {
            "blendShape": self.blend_shape,
            "weight": self.weight,
            "duration": self.duration,
            "delay": self.delay,
        }


@dataclass
class AvatarIntent:
    """Complete parsed intent from LLM output — everything the avatar needs."""
    speech_text: str = ""
    emotion: Emotion = field(default_factory=Emotion)
    gestures: list[GestureCommand] = field(default_factory=list)
    gaze: GazeTarget = field(default_factory=GazeTarget)
    spatial: SpatialCommand | None = None
    micro_expressions: list[MicroExpression] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {
            "speechText": self.speech_text,
            "emotion": self.emotion.to_dict(),
            "gestures": [g.to_dict() for g in self.gestures],
            "gaze": self.gaze.to_dict(),
            "microExpressions": [m.to_dict() for m in self.micro_expressions],
        }
        if self.spatial:
            d["spatial"] = self.spatial.to_dict()
        return d


@dataclass
class UserState:
    """Tracked state of the user (from PSVR2/WebXR/webcam)."""
    head_position: Vec3 = field(default_factory=Vec3)
    head_rotation: Vec3 = field(default_factory=Vec3)  # euler angles
    left_hand_position: Vec3 | None = None
    right_hand_position: Vec3 | None = None
    body_position: Vec3 = field(default_factory=Vec3)

    def to_dict(self) -> dict:
        d: dict = {
            "headPosition": self.head_position.to_dict(),
            "headRotation": self.head_rotation.to_dict(),
            "bodyPosition": self.body_position.to_dict(),
        }
        if self.left_hand_position:
            d["leftHandPosition"] = self.left_hand_position.to_dict()
        if self.right_hand_position:
            d["rightHandPosition"] = self.right_hand_position.to_dict()
        return d
