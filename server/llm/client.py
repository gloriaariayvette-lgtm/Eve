"""Streaming LLM client for OpenAI-compatible endpoints (LM Studio, ollama, etc.).

Phase 4: Now integrates with ConversationMemory for context-aware history
and build_system_prompt for personality/state-aware prompting.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from server.config import settings
from server.llm.prompts import SYSTEM_PROMPT, build_system_prompt

log = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
        self.model = settings.llm_model
        self.conversation_history: list[dict[str, str]] = []
        self.max_history = 20  # keep last N turns

        # Phase 4: dynamic system prompt (updated per turn)
        self._system_prompt = SYSTEM_PROMPT

    def set_system_prompt(self, prompt: str) -> None:
        """Update the system prompt (called by pipeline with personality/state context)."""
        self._system_prompt = prompt

    def set_context_history(self, messages: list[dict[str, str]]) -> None:
        """Replace conversation history with context from ConversationMemory."""
        self.conversation_history = messages

    async def chat_stream(self, user_message: str) -> AsyncIterator[str]:
        """Stream LLM response tokens. Yields text chunks as they arrive."""
        self.conversation_history.append({"role": "user", "content": user_message})

        # Trim history to avoid context overflow
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        messages = [
            {"role": "system", "content": self._system_prompt},
            *self.conversation_history,
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                stream=True,
            )

            full_response = ""
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_response += delta.content
                    yield delta.content

            # Store assistant response in history
            self.conversation_history.append({"role": "assistant", "content": full_response})

        except Exception as e:
            log.error("LLM stream error: %s", e)
            error_msg = "[EMOTION: neutral | INTENSITY: 0.3]\n[GESTURE: none]\n[GAZE: user_eyes]\nI'm having trouble thinking right now. Give me a moment."
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            yield error_msg

    async def chat(self, user_message: str) -> str:
        """Non-streaming chat. Returns full response."""
        chunks: list[str] = []
        async for chunk in self.chat_stream(user_message):
            chunks.append(chunk)
        return "".join(chunks)

    def reset(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
