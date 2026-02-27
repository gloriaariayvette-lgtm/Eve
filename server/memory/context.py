"""Conversation memory — sliding-window context with topic tracking and summary.

Maintains a structured memory of the conversation:
  - Recent turns (full detail, used for LLM context)
  - Topic history (what subjects have been discussed)
  - Emotional trajectory (how the conversation's emotional tone evolved)
  - Key facts extracted from user messages (name, preferences, etc.)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ConversationTurn:
    """A single user ↔ avatar exchange."""
    role: Literal["user", "assistant"]
    text: str
    timestamp: float = field(default_factory=time.time)
    emotion_primary: str = "neutral"
    emotion_valence: float = 0.0
    emotion_arousal: float = 0.2
    topics: list[str] = field(default_factory=list)


@dataclass
class UserFact:
    """An extracted fact about the user."""
    key: str           # e.g. "name", "favorite_color", "job"
    value: str
    confidence: float  # 0-1
    turn_number: int
    timestamp: float = field(default_factory=time.time)


class ConversationMemory:
    """Manages conversation history with structured memory layers."""

    def __init__(self, max_recent: int = 30, max_summary_turns: int = 100) -> None:
        self.recent_turns: list[ConversationTurn] = []
        self.max_recent = max_recent
        self.max_summary_turns = max_summary_turns

        # Topic tracking
        self.active_topics: list[str] = []
        self.topic_history: list[tuple[str, int]] = []  # (topic, turn_number)

        # User facts
        self.user_facts: dict[str, UserFact] = {}

        # Conversation summary (compressed older context)
        self.summary: str = ""
        self._summarized_up_to: int = 0

        # Timing
        self.session_start = time.time()
        self.last_user_message_time = 0.0
        self.total_turns = 0

    @property
    def turn_count(self) -> int:
        return self.total_turns

    @property
    def silence_duration(self) -> float:
        """Seconds since last user message."""
        if self.last_user_message_time == 0:
            return 0.0
        return time.time() - self.last_user_message_time

    @property
    def session_duration(self) -> float:
        """Seconds since session start."""
        return time.time() - self.session_start

    def add_turn(
        self,
        role: Literal["user", "assistant"],
        text: str,
        emotion_primary: str = "neutral",
        emotion_valence: float = 0.0,
        emotion_arousal: float = 0.2,
    ) -> None:
        """Record a conversation turn."""
        self.total_turns += 1

        # Extract topics from text
        topics = self._extract_topics(text)

        turn = ConversationTurn(
            role=role,
            text=text,
            emotion_primary=emotion_primary,
            emotion_valence=emotion_valence,
            emotion_arousal=emotion_arousal,
            topics=topics,
        )

        self.recent_turns.append(turn)

        if role == "user":
            self.last_user_message_time = time.time()
            self._extract_user_facts(text)

        # Update topic tracking
        for topic in topics:
            if topic not in self.active_topics:
                self.active_topics.append(topic)
                self.topic_history.append((topic, self.total_turns))

        # Prune active topics (keep last 5)
        if len(self.active_topics) > 5:
            self.active_topics = self.active_topics[-5:]

        # Compress old turns into summary when window gets large
        if len(self.recent_turns) > self.max_recent:
            self._compress_to_summary()

    def get_context_for_llm(self) -> list[dict[str, str]]:
        """Get conversation history formatted for LLM context window."""
        messages: list[dict[str, str]] = []

        # Include summary if available
        if self.summary:
            messages.append({
                "role": "system",
                "content": f"[Previous conversation summary: {self.summary}]",
            })

        # Include recent turns
        for turn in self.recent_turns:
            messages.append({
                "role": turn.role,
                "content": turn.text,
            })

        return messages

    def get_user_context_string(self) -> str:
        """Get a string of known user facts for LLM context."""
        if not self.user_facts:
            return ""

        facts = []
        for fact in self.user_facts.values():
            if fact.confidence >= 0.5:
                facts.append(f"- {fact.key}: {fact.value}")

        if not facts:
            return ""

        return "Known about the user:\n" + "\n".join(facts)

    def get_recent_emotion_summary(self, n: int = 5) -> dict[str, float]:
        """Average emotion values over last N turns."""
        recent = [t for t in self.recent_turns[-n:] if t.role == "assistant"]
        if not recent:
            return {"valence": 0.0, "arousal": 0.2}

        avg_valence = sum(t.emotion_valence for t in recent) / len(recent)
        avg_arousal = sum(t.emotion_arousal for t in recent) / len(recent)
        return {"valence": avg_valence, "arousal": avg_arousal}

    def _extract_topics(self, text: str) -> list[str]:
        """Simple keyword-based topic extraction."""
        topics: list[str] = []
        text_lower = text.lower()

        topic_keywords: dict[str, list[str]] = {
            "work": ["work", "job", "career", "office", "boss", "colleague", "project"],
            "family": ["family", "parent", "mother", "father", "sister", "brother", "child", "kid"],
            "health": ["health", "sick", "doctor", "exercise", "sleep", "tired", "pain"],
            "hobbies": ["hobby", "game", "music", "movie", "book", "sport", "cook", "travel"],
            "feelings": ["feel", "emotion", "happy", "sad", "angry", "anxious", "stressed", "worried"],
            "relationships": ["friend", "partner", "relationship", "date", "love", "breakup"],
            "goals": ["goal", "dream", "plan", "future", "want to", "hope", "wish"],
            "memories": ["remember", "memory", "when i was", "used to", "childhood", "past"],
            "daily_life": ["today", "yesterday", "morning", "evening", "weekend", "routine"],
            "technology": ["computer", "phone", "app", "software", "internet", "code", "program"],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)

        return topics[:3]  # max 3 topics per message

    def _extract_user_facts(self, text: str) -> None:
        """Extract factual information about the user from their messages."""
        text_lower = text.lower()

        # Name patterns
        name_patterns = [
            r"(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+)",
            r"(?:name's)\s+([A-Z][a-z]+)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.user_facts["name"] = UserFact(
                    key="name",
                    value=match.group(1).title(),
                    confidence=0.8,
                    turn_number=self.total_turns,
                )
                break

        # Preference patterns
        pref_patterns = [
            (r"i (?:really )?(?:love|like|enjoy|adore)\s+(.+?)(?:\.|,|!|$)", "likes"),
            (r"i (?:hate|dislike|can't stand)\s+(.+?)(?:\.|,|!|$)", "dislikes"),
            (r"my favorite (\w+) is (.+?)(?:\.|,|!|$)", "favorite_{0}"),
        ]
        for pattern, key_template in pref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if "{0}" in key_template:
                    key = key_template.format(match.group(1).lower())
                    value = match.group(2).strip()
                else:
                    key = key_template
                    value = match.group(1).strip()

                # Only store if reasonably short (not a full sentence)
                if len(value) < 50:
                    self.user_facts[key] = UserFact(
                        key=key,
                        value=value,
                        confidence=0.6,
                        turn_number=self.total_turns,
                    )

    def _compress_to_summary(self) -> None:
        """Compress older turns into a text summary."""
        # Take the oldest half of recent turns and summarize
        split = len(self.recent_turns) // 2
        old_turns = self.recent_turns[:split]
        self.recent_turns = self.recent_turns[split:]

        # Build summary from old turns
        fragments: list[str] = []
        for turn in old_turns:
            speaker = "User" if turn.role == "user" else "Eve"
            # Keep it brief
            short_text = turn.text[:80] + ("..." if len(turn.text) > 80 else "")
            fragments.append(f"{speaker}: {short_text}")

        new_section = "; ".join(fragments)

        if self.summary:
            self.summary = f"{self.summary} | Then: {new_section}"
        else:
            self.summary = new_section

        # Keep summary from growing unbounded
        if len(self.summary) > 1000:
            self.summary = self.summary[-800:]

    def reset(self) -> None:
        """Clear all memory."""
        self.recent_turns.clear()
        self.active_topics.clear()
        self.topic_history.clear()
        self.user_facts.clear()
        self.summary = ""
        self._summarized_up_to = 0
        self.total_turns = 0
        self.session_start = time.time()
        self.last_user_message_time = 0.0
