import os

BICEP = os.path.join(os.path.dirname(__file__), "..", "infra", "main.bicep")

def test_bicep_exists():
    assert os.path.exists(BICEP)

def test_bicep_hardening_present():
    text = open(BICEP).read()
    assert "disableLocalAuth: true" in text
    assert "customSubDomainName" in text
    assert "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" in text  # Cognitive Services OpenAI User
    assert "userAssignedIdentities" in text
    assert "output endpoint" in text
