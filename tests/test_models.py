import json
import pytest
from pydantic import ValidationError
from api.models import (
    Urgency, DisputeTriage, TriageRequest, BenchmarkRequest, Usage,
)

def test_dispute_triage_valid():
    t = DisputeTriage(category="card_fraud", urgency="high",
                      needs_human_review=True, suggested_next_action="Freeze card", pii_detected=True)
    assert t.urgency is Urgency.high

def test_dispute_triage_rejects_extra_field():
    with pytest.raises(ValidationError):
        DisputeTriage(category="other", urgency="low", needs_human_review=False,
                      suggested_next_action="x", pii_detected=False, confidence=0.9)

def test_dispute_triage_strict_no_coercion():
    with pytest.raises(ValidationError):
        DisputeTriage(category="other", urgency="low", needs_human_review="yes",  # str -> bool refused
                      suggested_next_action="x", pii_detected=False)

def test_triage_request_requires_nonempty_text():
    with pytest.raises(ValidationError):
        TriageRequest(dispute_text="")

def test_triage_request_fail_first_k_bounds():
    with pytest.raises(ValidationError):
        TriageRequest(dispute_text="hi", fail_first_k=99)

def test_usage_total():
    assert Usage(prompt_tokens=3, completion_tokens=4).total == 7

def test_benchmark_request_n_bounds():
    with pytest.raises(ValidationError):
        BenchmarkRequest(providers=["mock"], n=1, dispute_text="x")

def test_triage_request_strict_rejects_type_coercion():
    # STRICT_IN input contract: a string is NOT coerced to int
    with pytest.raises(ValidationError):
        TriageRequest(dispute_text="hi", fail_first_k="2")

def test_dispute_triage_accepts_string_enum_from_json():
    # FORBID (not strict): the LLM's JSON reply carries urgency as a string
    data = json.loads('{"category":"atm","urgency":"medium","needs_human_review":false,'
                      '"suggested_next_action":"x","pii_detected":false}')
    t = DisputeTriage.model_validate(data)
    assert t.urgency is Urgency.medium
