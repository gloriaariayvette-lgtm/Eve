"""Emotion model — maps text sentiment to Valence-Arousal-Dominance.

Fast, local, no ML dependencies. Uses keyword matching + heuristics
for real-time emotion extraction when the LLM doesn't provide tags.
"""

from __future__ import annotations

import re

from server.intent.schema import Emotion, PrimaryEmotion

# Keyword → (primary_emotion, valence, arousal, dominance)
_KEYWORD_MAP: dict[str, tuple[PrimaryEmotion, float, float, float]] = {
    # Joy / positive
    "happy": (PrimaryEmotion.JOY, 0.8, 0.6, 0.6),
    "glad": (PrimaryEmotion.JOY, 0.6, 0.5, 0.5),
    "excited": (PrimaryEmotion.JOY, 0.7, 0.9, 0.6),
    "wonderful": (PrimaryEmotion.JOY, 0.9, 0.6, 0.5),
    "great": (PrimaryEmotion.JOY, 0.7, 0.5, 0.6),
    "love": (PrimaryEmotion.TENDERNESS, 0.8, 0.4, 0.4),
    "beautiful": (PrimaryEmotion.TENDERNESS, 0.7, 0.3, 0.4),
    "laugh": (PrimaryEmotion.JOY, 0.8, 0.7, 0.5),
    "smile": (PrimaryEmotion.JOY, 0.6, 0.4, 0.5),
    "amazing": (PrimaryEmotion.JOY, 0.8, 0.7, 0.5),
    "thank": (PrimaryEmotion.TENDERNESS, 0.6, 0.3, 0.4),
    "enjoy": (PrimaryEmotion.JOY, 0.6, 0.5, 0.5),
    "fun": (PrimaryEmotion.JOY, 0.7, 0.6, 0.5),

    # Sadness
    "sad": (PrimaryEmotion.SADNESS, -0.7, 0.3, 0.2),
    "sorry": (PrimaryEmotion.SADNESS, -0.5, 0.3, 0.3),
    "miss": (PrimaryEmotion.SADNESS, -0.5, 0.3, 0.3),
    "lonely": (PrimaryEmotion.SADNESS, -0.7, 0.2, 0.2),
    "cry": (PrimaryEmotion.SADNESS, -0.8, 0.5, 0.2),
    "hurt": (PrimaryEmotion.SADNESS, -0.7, 0.4, 0.2),
    "lost": (PrimaryEmotion.SADNESS, -0.5, 0.3, 0.3),
    "unfortunately": (PrimaryEmotion.SADNESS, -0.4, 0.3, 0.3),

    # Anger
    "angry": (PrimaryEmotion.ANGER, -0.7, 0.8, 0.8),
    "furious": (PrimaryEmotion.ANGER, -0.9, 0.9, 0.8),
    "annoyed": (PrimaryEmotion.ANGER, -0.4, 0.5, 0.6),
    "frustrat": (PrimaryEmotion.ANGER, -0.5, 0.6, 0.5),
    "hate": (PrimaryEmotion.ANGER, -0.8, 0.7, 0.7),

    # Surprise
    "surprise": (PrimaryEmotion.SURPRISE, 0.3, 0.8, 0.4),
    "wow": (PrimaryEmotion.SURPRISE, 0.4, 0.8, 0.4),
    "unexpected": (PrimaryEmotion.SURPRISE, 0.1, 0.7, 0.4),
    "really": (PrimaryEmotion.SURPRISE, 0.2, 0.5, 0.4),
    "incredible": (PrimaryEmotion.SURPRISE, 0.5, 0.7, 0.4),

    # Fear
    "afraid": (PrimaryEmotion.FEAR, -0.7, 0.7, 0.2),
    "scared": (PrimaryEmotion.FEAR, -0.7, 0.7, 0.2),
    "worry": (PrimaryEmotion.FEAR, -0.5, 0.6, 0.3),
    "anxious": (PrimaryEmotion.FEAR, -0.5, 0.6, 0.3),
    "nervous": (PrimaryEmotion.FEAR, -0.4, 0.6, 0.3),
    "danger": (PrimaryEmotion.FEAR, -0.6, 0.7, 0.3),

    # Interest
    "interesting": (PrimaryEmotion.INTEREST, 0.4, 0.5, 0.5),
    "curious": (PrimaryEmotion.INTEREST, 0.3, 0.5, 0.5),
    "fascin": (PrimaryEmotion.INTEREST, 0.5, 0.6, 0.5),
    "wonder": (PrimaryEmotion.INTEREST, 0.4, 0.5, 0.5),
    "tell me": (PrimaryEmotion.INTEREST, 0.3, 0.5, 0.5),
    "how": (PrimaryEmotion.INTEREST, 0.2, 0.4, 0.5),
    "think": (PrimaryEmotion.INTEREST, 0.2, 0.4, 0.5),

    # Disgust
    "disgust": (PrimaryEmotion.DISGUST, -0.6, 0.5, 0.6),
    "gross": (PrimaryEmotion.DISGUST, -0.6, 0.5, 0.6),
    "terrible": (PrimaryEmotion.DISGUST, -0.7, 0.5, 0.5),
    "awful": (PrimaryEmotion.DISGUST, -0.7, 0.5, 0.5),
}

# Punctuation-based arousal modifiers
_EXCLAMATION_BOOST = 0.15
_QUESTION_BOOST = 0.05
_CAPS_BOOST = 0.1


def analyze_text(text: str) -> Emotion:
    """Analyze text and return VAD emotion. Fast keyword-based approach."""
    text_lower = text.lower()
    words = re.findall(r'\w+', text_lower)

    # Accumulate emotion signals
    total_valence = 0.0
    total_arousal = 0.0
    total_dominance = 0.0
    match_count = 0
    detected_primary = PrimaryEmotion.NEUTRAL

    for keyword, (primary, v, a, d) in _KEYWORD_MAP.items():
        if keyword in text_lower:
            total_valence += v
            total_arousal += a
            total_dominance += d
            match_count += 1
            # Primary emotion = strongest match (first found, could be improved)
            if match_count == 1:
                detected_primary = primary

    if match_count > 0:
        total_valence /= match_count
        total_arousal /= match_count
        total_dominance /= match_count
    else:
        total_valence = 0.0
        total_arousal = 0.2
        total_dominance = 0.5

    # Punctuation modifiers
    exclamation_count = text.count("!")
    question_count = text.count("?")
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

    total_arousal += min(exclamation_count * _EXCLAMATION_BOOST, 0.3)
    total_arousal += min(question_count * _QUESTION_BOOST, 0.1)
    if caps_ratio > 0.5 and len(words) > 2:
        total_arousal += _CAPS_BOOST
        total_dominance += 0.1

    # Clamp
    total_valence = max(-1.0, min(1.0, total_valence))
    total_arousal = max(0.0, min(1.0, total_arousal))
    total_dominance = max(0.0, min(1.0, total_dominance))

    return Emotion(
        valence=round(total_valence, 3),
        arousal=round(total_arousal, 3),
        dominance=round(total_dominance, 3),
        primary=detected_primary,
    )
