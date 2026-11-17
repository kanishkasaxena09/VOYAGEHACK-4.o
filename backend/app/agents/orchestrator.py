import json
import re
from datetime import date
from typing import Any, Dict, Optional, Type, TypeVar
from groq import AsyncGroq
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self._client: Optional[AsyncGroq] = None
        
        # Only initialize if a genuine, non-dummy key is supplied
        if self.api_key and self.api_key.strip() and self.api_key not in [
            "your_groq_api_key_here", "change_me", "None", ""
        ] and not self.api_key.startswith("your_"):
            try:
                self._client = AsyncGroq(api_key=self.api_key, timeout=5.0)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2
    ) -> str:
        """Call Groq API or return empty string to trigger deterministic fallback."""
        if self.is_available:
            try:
                chat_completion = await self._client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model,
                    temperature=temperature,
                    max_tokens=1500
                )
                return chat_completion.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"Groq API call error or timeout: {e}. Falling back to deterministic NLP logic.")
        return ""

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T]
    ) -> Optional[T]:
        """Calls Groq expecting JSON conforming to response_model."""
        if not self.is_available:
            return None

        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        augmented_system = (
            f"{system_prompt}\n\n"
            f"You MUST respond ONLY with a valid JSON object strictly matching this JSON schema:\n"
            f"{schema_json}\n"
            f"Do not include markdown codeblocks or explanations outside the JSON."
        )

        try:
            content = await self.generate_completion(augmented_system, user_prompt, temperature=0.1)
            if not content:
                return None

            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)
            return response_model.model_validate(parsed)
        except Exception as e:
            logger.warning(f"Failed to generate structured LLM response: {e}")
            return None


llm_client = LLMClient()
