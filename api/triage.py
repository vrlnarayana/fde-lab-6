from __future__ import annotations
import json
from pydantic import ValidationError
from api.models import DisputeTriage

SYSTEM_PROMPT = (
    "You are a UK retail bank's dispute-triage assistant. Read the customer's free-text "
    "dispute and return ONLY a JSON object with exactly these keys: "
    "category (one of: card_fraud, duplicate_charge, subscription, atm, other), "
    "urgency (one of: low, medium, high), needs_human_review (boolean), "
    "suggested_next_action (string), pii_detected (boolean — true if the text contains PII "
    "to redact before logging). No prose, no markdown — JSON only."
)


def build_messages(dispute_text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": dispute_text},
    ]


def parse_triage(raw_json: str) -> tuple[DisputeTriage | None, str | None]:
    """Validate a raw model reply into a DisputeTriage. Never raises."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return None, f"reply is not valid JSON: {exc}"
    try:
        return DisputeTriage.model_validate(data), None
    except ValidationError as exc:
        return None, f"reply failed validation: {exc.errors(include_url=False)}"
