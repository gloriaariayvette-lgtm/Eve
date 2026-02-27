"""Personality system — configurable avatar personas using trait-based behavior modifiers.

Based on a simplified Big Five personality model:
  - Openness:        curiosity, creativity, preference for novelty
  - Conscientiousness: organization, dependability, discipline
  - Extraversion:    sociability, assertiveness, positive emotion
  - Agreeableness:   cooperation, trust, empathy
  - Neuroticism:     emotional instability, anxiety, moodiness

Each trait (0.0 to 1.0) influences gesture selection, spatial behavior,
gaze patterns, emotional expression intensity, and speaking style.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PersonalityTraits:
    """Big Five personality traits, each 0.0 to 1.0."""
    openness: float = 0.6
    conscientiousness: float = 0.5
    extraversion: float = 0.6
    agreeableness: float = 0.7
    neuroticism: float = 0.3

    def validate(self) -> PersonalityTraits:
        """Clamp all values to 0-1 range."""
        self.openness = max(0.0, min(1.0, self.openness))
        self.conscientiousness = max(0.0, min(1.0, self.conscientiousness))
        self.extraversion = max(0.0, min(1.0, self.extraversion))
        self.agreeableness = max(0.0, min(1.0, self.agreeableness))
        self.neuroticism = max(0.0, min(1.0, self.neuroticism))
        return self


@dataclass
class PersonalityModifiers:
    """Computed behavior modifiers derived from personality traits."""
    # Gesture
    gesture_frequency: float = 1.0    # how often to gesture (0.5-1.5)
    gesture_amplitude: float = 1.0    # how big gestures are (0.5-1.5)

    # Spatial
    preferred_distance: float = 1.5   # meters — introverts farther, extroverts closer
    approach_willingness: float = 0.5 # 0 = never approach, 1 = eagerly approach

    # Gaze
    eye_contact_duration: float = 0.7 # how long to maintain eye contact before breaking
    gaze_aversion_rate: float = 0.2   # how often to look away

    # Expression
    expression_intensity: float = 1.0  # how strongly to show facial expressions
    emotional_reactivity: float = 1.0  # how quickly to react to emotional content

    # Voice/Speech
    speaking_pace: float = 1.0        # speech rate modifier
    pause_frequency: float = 0.3      # how often to pause (contemplative)

    # Behavioral
    mirroring_strength: float = 0.5   # how much to mirror user behavior
    initiative: float = 0.5           # willingness to take conversational lead


@dataclass
class Personality:
    """Complete personality profile with traits and computed modifiers."""
    name: str
    description: str
    traits: PersonalityTraits
    modifiers: PersonalityModifiers

    # Optional: system prompt addition for this personality
    prompt_addition: str = ""


def compute_modifiers(traits: PersonalityTraits) -> PersonalityModifiers:
    """Derive behavior modifiers from personality traits."""
    t = traits

    # Extraversion drives expressiveness and closeness
    gesture_frequency = 0.5 + t.extraversion * 1.0
    gesture_amplitude = 0.6 + t.extraversion * 0.6
    preferred_distance = 2.0 - t.extraversion * 0.8  # 1.2m (extrovert) to 2.0m (introvert)
    approach_willingness = t.extraversion * 0.7 + t.agreeableness * 0.3

    # Agreeableness drives warmth and mirroring
    eye_contact_duration = 0.4 + t.agreeableness * 0.5
    mirroring_strength = 0.2 + t.agreeableness * 0.6
    expression_intensity = 0.5 + t.agreeableness * 0.3 + t.extraversion * 0.2

    # Neuroticism drives reactivity and gaze patterns
    emotional_reactivity = 0.5 + t.neuroticism * 0.5
    gaze_aversion_rate = 0.1 + t.neuroticism * 0.3

    # Openness drives initiative and speaking patterns
    initiative = 0.3 + t.openness * 0.4 + t.extraversion * 0.3
    pause_frequency = 0.1 + t.openness * 0.3  # open = more contemplative pauses

    # Conscientiousness drives pace and precision
    speaking_pace = 0.8 + t.conscientiousness * 0.3

    return PersonalityModifiers(
        gesture_frequency=round(gesture_frequency, 2),
        gesture_amplitude=round(gesture_amplitude, 2),
        preferred_distance=round(preferred_distance, 2),
        approach_willingness=round(approach_willingness, 2),
        eye_contact_duration=round(eye_contact_duration, 2),
        gaze_aversion_rate=round(gaze_aversion_rate, 2),
        expression_intensity=round(expression_intensity, 2),
        emotional_reactivity=round(emotional_reactivity, 2),
        speaking_pace=round(speaking_pace, 2),
        pause_frequency=round(pause_frequency, 2),
        mirroring_strength=round(mirroring_strength, 2),
        initiative=round(initiative, 2),
    )


# --- Preset Personalities ---

def create_personality(name: str, traits: PersonalityTraits, description: str = "", prompt_addition: str = "") -> Personality:
    """Create a personality with auto-computed modifiers."""
    traits = traits.validate()
    return Personality(
        name=name,
        description=description,
        traits=traits,
        modifiers=compute_modifiers(traits),
        prompt_addition=prompt_addition,
    )


# Default: warm, empathetic, moderately expressive
DEFAULT_PERSONALITY = create_personality(
    "Eve",
    PersonalityTraits(openness=0.7, conscientiousness=0.5, extraversion=0.6, agreeableness=0.8, neuroticism=0.2),
    description="Warm and empathetic companion. Attentive listener with gentle expressiveness.",
    prompt_addition="You are warm, empathetic, and genuinely curious about people. You listen actively and respond with care.",
)

# Energetic and playful
ENERGETIC_PERSONALITY = create_personality(
    "Spark",
    PersonalityTraits(openness=0.8, conscientiousness=0.4, extraversion=0.9, agreeableness=0.7, neuroticism=0.2),
    description="High-energy, playful, and enthusiastic. Loves to joke and be expressive.",
    prompt_addition="You are energetic, playful, and enthusiastic. You love to make people laugh and feel good.",
)

# Calm and thoughtful
SERENE_PERSONALITY = create_personality(
    "Sage",
    PersonalityTraits(openness=0.8, conscientiousness=0.7, extraversion=0.3, agreeableness=0.7, neuroticism=0.1),
    description="Calm, thoughtful, and wise. Speaks deliberately and listens deeply.",
    prompt_addition="You are calm and contemplative. You choose your words carefully and give space for silence.",
)

# Shy but warm
SHY_PERSONALITY = create_personality(
    "Whisper",
    PersonalityTraits(openness=0.5, conscientiousness=0.6, extraversion=0.2, agreeableness=0.8, neuroticism=0.5),
    description="Shy and gentle. Warms up over time, deeply empathetic once comfortable.",
    prompt_addition="You are initially shy and speak softly. As you grow comfortable you open up more. You are deeply caring.",
)

PERSONALITY_PRESETS: dict[str, Personality] = {
    "eve": DEFAULT_PERSONALITY,
    "spark": ENERGETIC_PERSONALITY,
    "sage": SERENE_PERSONALITY,
    "whisper": SHY_PERSONALITY,
}
