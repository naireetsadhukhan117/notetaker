"""
GenerationEngine
----------------
I/O-bound Retrieval-Augmented Generation.
Supports Groq and OpenRouter via an OpenAI-compatible client interface.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

_SYSTEM_DIRECTIVE = """You are a study-notes assistant.
When context includes a valid image reference path, you MUST embed it using standard
Markdown notation exactly as: ![description](local_path)
If the reference says 'None', do not attempt to add or generate an image link.
Never omit or alter local_path values. Produce clean, structured Markdown."""

Provider = Literal["groq", "openrouter"]

_PROVIDER_BASES: Dict[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

_DEFAULT_MODELS: Dict[str, str] = {
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "openrouter/free",
}


class GenerationEngine:
    """Generates structured notes and quizzes from semantic retrieval contexts."""

    def __init__(
        self,
        provider: Provider = "groq",
        api_key:  str = "",
        model:    Optional[str] = None,
    ):
        if provider not in _PROVIDER_BASES:
            raise ValueError(f"Unsupported infrastructure provider requested: '{provider}'")
            
        self.provider = provider
        self.model    = model or _DEFAULT_MODELS[provider]
        self._client  = self._build_client(provider, api_key)

    def generate_notes(self, query: str, context_results: List[Dict], max_tokens: int = 2048) -> str:
        if not context_results:
            return "> **No context available.** The query topic was not found in the knowledge base."

        user_prompt = self._build_user_prompt(query, context_results)

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",  "content": _SYSTEM_DIRECTIVE},
                    {"role": "user",    "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            
            if not response.choices or len(response.choices) == 0:
                return "> **Error:** The cloud inference provider returned an empty response layout."

            return response.choices[0].message.content
        except Exception as exc:
            logger.error("GenerationEngine failed to synthesize study notes: %s", exc)
            raise

    def generate_quiz(self, context_results: List[Dict], num_questions: int = 5, max_tokens: int = 2048) -> str:
        if not context_results:
            return "> **No context available.** Cannot generate quiz."

        context_str  = self._build_context_block(context_results)
        quiz_prompt  = (
            f"Based on the following study material, create {num_questions} "
            f"multiple-choice questions with 4 options each. "
            f"Mark the correct answer with **(correct)**.\\n\\n"
            f"{context_str}"
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",  "content": _SYSTEM_DIRECTIVE},
                    {"role": "user",    "content": quiz_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.5,
            )
            
            if not response.choices or len(response.choices) == 0:
                return "> **Error:** The cloud inference provider failed to parse structural quiz responses."

            return response.choices[0].message.content
        except Exception as exc:
            logger.error("GenerationEngine failed to synthesize text quiz: %s", exc)
            raise

    def _build_user_prompt(self, query: str, results: List[Dict]) -> str:
        context_block = self._build_context_block(results)
        return (
            f"# User Query\\n{query}\\n\\n"
            f"# Retrieved Context\\n{context_block}\\n\\n"
            "Using ONLY the context above, produce comprehensive Markdown "
            "study notes that directly address the query."
        )

    @staticmethod
    def _build_context_block(results: List[Dict]) -> str:
        blocks: List[str] = []
        for r in results:
            meta        = r.get("metadata", {})
            chunk_id    = meta.get("chunk_id", "unknown")
            raw_path    = meta.get("local_path")
            local_path  = str(raw_path) if raw_path else "None"
            text        = r.get("text_content", "")

            block = (
                f"[Context ID: {chunk_id}]\\n"
                f"[Associated Image Reference on Disk: {local_path}]\\n"
                f"Source Text: {text}"
            )
            blocks.append(block)

        return "\\n\\n---\\n\\n".join(blocks)

    @staticmethod
    def _build_client(provider: Provider, api_key: str):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "The core 'openai' SDK package is missing. Run: pip install openai"
            ) from exc

        base_url = _PROVIDER_BASES.get(provider)
        extra_headers = {}

        return OpenAI(
            api_key=api_key, 
            base_url=base_url,
            default_headers=extra_headers if extra_headers else None
        )