from __future__ import annotations
from api.config import Settings
from api.errors import ProviderError
from api.models import TriageRequest, ProviderTriageRaw, Usage
from api.triage import build_messages


class OpenAIDirectProvider:
    """Direct OpenAI — used only by the 6-D latency/cost drill (US default, API key)."""
    name = "openai"
    is_mock = False
    auth_mode = "api-key"

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY not set")
        from openai import AsyncOpenAI  # lazy
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=build_messages(request.dispute_text),
            response_format={"type": "json_object"},
            timeout=10,
        )
        usage = resp.usage
        return ProviderTriageRaw(
            model=resp.model,
            content=resp.choices[0].message.content or "",
            usage=Usage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            ),
        )
