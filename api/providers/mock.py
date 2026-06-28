from __future__ import annotations
import json
from api.errors import TransientError
from api.models import TriageRequest, ProviderTriageRaw, Usage


def _classify(text: str) -> dict:
    t = text.lower()
    pii = any(ch.isdigit() for ch in text) or "£" in text
    if any(k in t for k in ("never authorised", "didn't authorise", "did not authorise",
                            "unauthor", "fraud", "don't recognise", "do not recognise")):
        category, urgency, action = "card_fraud", "high", "Freeze the card and open a fraud case."
    elif any(k in t for k in ("twice", "duplicate", "two times", "double charged")):
        category, urgency, action = "duplicate_charge", "medium", "Check for a duplicate authorisation and refund if confirmed."
    elif any(k in t for k in ("subscription", "renew", "recurring")):
        category, urgency, action = "subscription", "low", "Locate the recurring mandate and offer cancellation."
    elif any(k in t for k in ("atm", "cash machine", "withdraw")):
        category, urgency, action = "atm", "medium", "Pull ATM journal for the terminal and timestamp."
    else:
        category, urgency, action = "other", "low", "Route to general disputes queue for review."
    needs_human = urgency == "high" or pii
    return {
        "category": category,
        "urgency": urgency,
        "needs_human_review": needs_human,
        "suggested_next_action": action,
        "pii_detected": pii,
    }


class MockProvider:
    """Deterministic, offline triage — the teaching engine.

    fail_first_k:    raise TransientError on the first k calls (retry/backoff demo).
    force_bad_output: emit malformed JSON (the 'Validate it' failure demo).
    """
    name = "mock"
    is_mock = True
    auth_mode = "n/a"

    def __init__(self, fail_first_k: int = 0, force_bad_output: bool = False):
        self._fails_left = fail_first_k
        self.force_bad_output = force_bad_output

    async def triage(self, request: TriageRequest) -> ProviderTriageRaw:
        if self._fails_left > 0:
            self._fails_left -= 1
            raise TransientError("429 rate limited (mock)")
        text = request.dispute_text
        content = "{not valid json" if self.force_bad_output else json.dumps(_classify(text))
        return ProviderTriageRaw(
            model="mock-triage-1",
            content=content,
            usage=Usage(prompt_tokens=len(text.split()), completion_tokens=12),
        )
