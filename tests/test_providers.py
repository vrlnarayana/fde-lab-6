import pytest
from api.config import Settings
from api.errors import ProviderError
from api.providers import available_providers, make_provider, auth_posture
from api.providers.mock import MockProvider

def offline_settings(**kw):
    base = dict(azure_openai_api_key=None, azure_openai_endpoint=None,
                openai_api_key=None, default_provider="mock", auth_mode="key")
    base.update(kw)
    return Settings(**base)

def test_mock_always_available():
    rows = {r["name"]: r for r in available_providers(offline_settings())}
    assert rows["mock"]["available"] is True
    assert rows["azure"]["available"] is False
    assert rows["openai"]["available"] is False

def test_make_provider_defaults_to_mock():
    p = make_provider(None, offline_settings())
    assert isinstance(p, MockProvider)

def test_make_provider_unknown_raises():
    with pytest.raises(ProviderError):
        make_provider("gemini", offline_settings())

def test_make_provider_unconfigured_azure_raises():
    with pytest.raises(ProviderError):
        make_provider("azure", offline_settings())

def test_force_bad_output_routes_through_mock():
    p = make_provider("azure", offline_settings(), force_bad_output=True)
    assert isinstance(p, MockProvider) and p.force_bad_output is True

def test_auth_posture_offline_is_simulated():
    post = auth_posture(offline_settings())
    assert post["simulated"] is True
    assert post["secrets_present"] is False
    assert post["region"] == "westeurope"

def test_auth_posture_azure_key_configured():
    s = offline_settings(azure_openai_api_key="k", azure_openai_endpoint="https://x.openai.azure.com", auth_mode="key")
    post = auth_posture(s)
    assert post["simulated"] is False
    assert post["mode"] == "api-key"
    assert post["secrets_present"] is True

def test_auth_posture_keyless_no_secret():
    s = offline_settings(azure_openai_endpoint="https://x.openai.azure.com", auth_mode="keyless")
    post = auth_posture(s)
    assert post["mode"] == "keyless"
    assert post["secrets_present"] is False
