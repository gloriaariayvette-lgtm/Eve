"""Viseme generation — maps text/phonemes to mouth shapes for lip sync.

Uses a text-based approximation (grapheme-to-viseme) since Piper doesn't
always expose phoneme timing. This gives us good-enough lip sync for
real-time avatar animation.

Viseme shapes follow the Oculus/Meta standard used by VRM:
  SILENT, PP, FF, TH, DD, KK, CH, SS, NN, RR, AA, EE, IH, OH, OO
"""

from __future__ import annotations

from server.intent.schema import Viseme, VisemeShape

# Grapheme clusters → viseme shape mapping
_GRAPHEME_VISEME: dict[str, VisemeShape] = {
    # Bilabial
    "p": VisemeShape.PP, "b": VisemeShape.PP, "m": VisemeShape.PP,
    # Labiodental
    "f": VisemeShape.FF, "v": VisemeShape.FF,
    # Dental
    "th": VisemeShape.TH,
    # Alveolar stops
    "t": VisemeShape.DD, "d": VisemeShape.DD,
    # Alveolar nasal/lateral
    "n": VisemeShape.NN, "l": VisemeShape.DD,
    # Velar
    "k": VisemeShape.KK, "g": VisemeShape.KK, "ng": VisemeShape.KK,
    # Post-alveolar
    "sh": VisemeShape.CH, "ch": VisemeShape.CH, "j": VisemeShape.CH,
    "zh": VisemeShape.CH,
    # Alveolar fricative
    "s": VisemeShape.SS, "z": VisemeShape.SS,
    # Rhotic
    "r": VisemeShape.RR,
    # Glottal
    "h": VisemeShape.SILENT,
    # Semivowels
    "w": VisemeShape.OO, "y": VisemeShape.EE,
}

# Vowel graphemes → viseme
_VOWEL_VISEME: dict[str, VisemeShape] = {
    "a": VisemeShape.AA,
    "e": VisemeShape.EE,
    "i": VisemeShape.IH,
    "o": VisemeShape.OH,
    "u": VisemeShape.OO,
    "ee": VisemeShape.EE,
    "oo": VisemeShape.OO,
    "ou": VisemeShape.OO,
    "ai": VisemeShape.AA,
    "ea": VisemeShape.EE,
    "oa": VisemeShape.OH,
    "ie": VisemeShape.EE,
    "ey": VisemeShape.EE,
    "ay": VisemeShape.AA,
    "ow": VisemeShape.OH,
}

# Average phoneme duration in seconds
_CONSONANT_DURATION = 0.06
_VOWEL_DURATION = 0.1
_PAUSE_DURATION = 0.15


def generate_visemes(text: str, speech_duration: float | None = None) -> list[Viseme]:
    """Generate a timed viseme sequence from text.

    If speech_duration is provided, visemes are stretched/compressed to fit.
    Otherwise, durations are estimated from text length.
    """
    if not text.strip():
        return []

    raw_visemes = _text_to_raw_visemes(text)

    if not raw_visemes:
        return []

    # Calculate total estimated duration
    total_estimated = sum(v.timestamp for v in raw_visemes)  # reusing timestamp as duration temp

    if total_estimated <= 0:
        return []

    # Scale to actual speech duration if provided
    if speech_duration and speech_duration > 0:
        scale = speech_duration / total_estimated
    else:
        scale = 1.0

    # Convert durations to absolute timestamps
    timed_visemes: list[Viseme] = []
    current_time = 0.0
    for v in raw_visemes:
        duration = v.timestamp * scale  # timestamp was holding duration
        timed_visemes.append(Viseme(
            shape=v.shape,
            weight=v.weight,
            timestamp=round(current_time, 4),
        ))
        current_time += duration

    # Append silent at end
    timed_visemes.append(Viseme(
        shape=VisemeShape.SILENT,
        weight=0.0,
        timestamp=round(current_time, 4),
    ))

    return timed_visemes


def _text_to_raw_visemes(text: str) -> list[Viseme]:
    """Convert text to a sequence of visemes with estimated durations.

    Returns visemes where .timestamp temporarily holds the duration.
    """
    visemes: list[Viseme] = []
    text = text.lower().strip()
    i = 0

    while i < len(text):
        char = text[i]

        # Skip non-alpha
        if not char.isalpha():
            if char in " ,;:.!?-":
                visemes.append(Viseme(
                    shape=VisemeShape.SILENT,
                    weight=0.0,
                    timestamp=_PAUSE_DURATION if char in ",.;:!?" else _PAUSE_DURATION * 0.3,
                ))
            i += 1
            continue

        # Try 2-char grapheme clusters first
        if i + 1 < len(text):
            digraph = text[i:i+2]
            if digraph in _GRAPHEME_VISEME:
                visemes.append(Viseme(
                    shape=_GRAPHEME_VISEME[digraph],
                    weight=0.8,
                    timestamp=_CONSONANT_DURATION,
                ))
                i += 2
                continue
            if digraph in _VOWEL_VISEME:
                visemes.append(Viseme(
                    shape=_VOWEL_VISEME[digraph],
                    weight=1.0,
                    timestamp=_VOWEL_DURATION,
                ))
                i += 2
                continue

        # Single character
        if char in _VOWEL_VISEME:
            visemes.append(Viseme(
                shape=_VOWEL_VISEME[char],
                weight=1.0,
                timestamp=_VOWEL_DURATION,
            ))
        elif char in _GRAPHEME_VISEME:
            visemes.append(Viseme(
                shape=_GRAPHEME_VISEME[char],
                weight=0.8,
                timestamp=_CONSONANT_DURATION,
            ))
        else:
            # Unknown character, treat as neutral
            visemes.append(Viseme(
                shape=VisemeShape.DD,
                weight=0.5,
                timestamp=_CONSONANT_DURATION,
            ))

        i += 1

    return visemes
