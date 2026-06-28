from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_providers_lists_mock_default_and_posture():
    data = client.get("/providers").json()
    names = {p["name"] for p in data["providers"]}
    assert {"mock", "azure", "openai"} <= names
    assert data["default"] == "mock"
    assert data["posture"]["simulated"] is True

def test_triage_happy_path_validated():
    r = client.post("/triage", json={"dispute_text": "I never authorised this £50 charge"})
    assert r.status_code == 200
    body = r.json()
    assert body["validated"] is True
    assert body["triage"]["category"] == "card_fraud"
    assert body["attempts"] == 1
    assert body["auth_mode"] == "n/a"

def test_triage_retry_demo_counts_attempts():
    r = client.post("/triage", json={"dispute_text": "hi", "fail_first_k": 2})
    assert r.status_code == 200
    assert r.json()["attempts"] == 3

def test_triage_malformed_output_is_unvalidated_not_500():
    r = client.post("/triage", json={"dispute_text": "x", "force_bad_output": True})
    assert r.status_code == 200
    body = r.json()
    assert body["validated"] is False
    assert body["triage"] is None
    assert body["error"]

def test_triage_unknown_provider_400():
    r = client.post("/triage", json={"dispute_text": "x", "provider": "gemini"})
    assert r.status_code == 400
    assert r.json()["detail"]["error_type"] == "ProviderError"

def test_triage_strict_rejects_extra_field_422():
    r = client.post("/triage", json={"dispute_text": "x", "temperature": 0.7})
    assert r.status_code == 422

def test_benchmark_mock_rows_simulated():
    r = client.post("/benchmark", json={"providers": ["mock"], "n": 6, "dispute_text": "twice charged"})
    assert r.status_code == 200
    data = r.json()
    assert data["rows"][0]["simulated"] is True
    assert "recommendation" in data

def test_authcheck_shape_offline():
    data = client.get("/authcheck").json()
    assert set(data["checklist"]) == {"resident_region", "keyless", "local_auth_disabled", "no_secrets_in_use"}
    # offline mock posture: region is westeurope (passes resident_region), not keyless, no secrets in use
    assert data["checklist"]["resident_region"] is True
    assert data["checklist"]["keyless"] is False
    assert data["checklist"]["no_secrets_in_use"] is True
    assert data["simulated"] is True
