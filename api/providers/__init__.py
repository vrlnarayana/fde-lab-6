from __future__ import annotations
from api.config import Settings
from api.errors import ProviderError
from api.providers.base import TriageProvider
from api.providers.mock import MockProvider


def _azure_ready(s: Settings) -> bool:
    if not s.azure_openai_endpoint:
        return False
    return s.auth_mode == "keyless" or bool(s.azure_openai_api_key)


def _availability(s: Settings) -> dict[str, bool]:
    return {"azure": _azure_ready(s), "openai": bool(s.openai_api_key)}


def available_providers(s: Settings) -> list[dict]:
    avail = _availability(s)
    rows = [{"name": "mock", "available": True, "is_mock": True, "auth_mode": "n/a"}]
    rows.append({"name": "azure", "available": avail["azure"], "is_mock": False,
                 "auth_mode": "keyless" if s.auth_mode == "keyless" else "api-key"})
    rows.append({"name": "openai", "available": avail["openai"], "is_mock": False, "auth_mode": "api-key"})
    return rows


def auth_posture(s: Settings) -> dict:
    azure_ready = _azure_ready(s)
    return {
        "mode": ("keyless" if s.auth_mode == "keyless" else "api-key") if azure_ready else "mock",
        "region": s.azure_region,
        "custom_subdomain": bool(s.azure_openai_endpoint and ".openai.azure.com" in s.azure_openai_endpoint),
        "disable_local_auth": s.azure_disable_local_auth,
        "secrets_present": bool(s.azure_openai_api_key or s.openai_api_key),
        "simulated": not azure_ready,
    }


def make_provider(name: str | None, s: Settings, *, fail_first_k: int = 0, force_bad_output: bool = False) -> TriageProvider:
    # Malformed-output is a deterministic teaching sim — always route through the mock.
    if name in (None, "mock") or force_bad_output:
        return MockProvider(fail_first_k=fail_first_k, force_bad_output=force_bad_output)

    avail = _availability(s)
    if name not in avail:
        raise ProviderError(f"unknown provider: {name}")
    if not avail[name]:
        raise ProviderError(f"provider '{name}' is not configured")

    if name == "azure":
        from api.providers.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider(s)
    if name == "openai":
        from api.providers.openai_direct import OpenAIDirectProvider
        return OpenAIDirectProvider(s)
    raise ProviderError(f"unknown provider: {name}")  # unreachable
