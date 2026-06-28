from api.triage import parse_triage, build_messages

VALID = ('{"category":"card_fraud","urgency":"high","needs_human_review":true,'
         '"suggested_next_action":"Freeze the card","pii_detected":true}')

def test_parse_valid():
    triage, err = parse_triage(VALID)
    assert err is None
    assert triage.category == "card_fraud"

def test_parse_not_json():
    triage, err = parse_triage("{not json")
    assert triage is None
    assert "JSON" in err

def test_parse_schema_violation():
    triage, err = parse_triage('{"category":"x","urgency":"SUPER","needs_human_review":true,'
                               '"suggested_next_action":"y","pii_detected":false}')
    assert triage is None
    assert "validation" in err.lower()

def test_build_messages_shape():
    msgs = build_messages("I was charged twice")
    assert msgs[0]["role"] == "system"
    assert msgs[-1]["role"] == "user"
    assert "charged twice" in msgs[-1]["content"]
