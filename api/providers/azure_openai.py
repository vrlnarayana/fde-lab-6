from __future__ import annotations
from api.config import Settings
from api.errors import ProviderError
from api.models import TriageRequest, ProviderTriageRaw, Usage
from api.triage import build_messages


class AzureOpenAIProvider:
    """Lab 6-A (api-key) and 6-B (keyless) — only the auth path differs."""
    name = "azure"
    is_mock = False

    def __init__(self, settings: Settings):
        if not settings.azure_openai_endpoint:
            raise ProviderError("AZURE_OPENAI_ENDPOINT not set")
        self.auth_mode = "keyless" if settings.auth_mode == "keyless" else "api-key"
        self._deployment = settings.azure_openai_deployment
        from openai import AsyncAzureOpenAI  # lazy

        if self.auth_mode == "keyless":
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider  # lazy
            token = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_ad_token_provider=token,        # identity, not a secret
                api_version="2024-12-01-preview",
            )
        else:
            if not settings.azure_openai_api_key:
                raise ProviderError("AZURE_OPENAI_API_KEY not set (auth_mode=key)")
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,  # REMOVED in Lab 6-B
                api_version="2024-12-01-preview",
            )

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw:
        resp = await self._client.chat.completions.create(
            model=self._deployment,
            messages=build_messages(request.dispute_text),
            response_format={"type": "json_object"},
            timeout=30,
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
