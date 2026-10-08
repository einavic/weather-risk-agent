import pytest
from pydantic import ValidationError

from app.agent.schema import FinalAnswer

VALID = {
    "answer": "Minneapolis is the most exposed Midwest hub to winter disruption.",
    "hubs": ["minneapolis"],
    "key_numbers": [{"hub_id": "minneapolis", "label": "winter score", "value": 94.3}],
    "caveat": "Scores count how often events happened, not how severe they were.",
}


def test_valid_answer_is_accepted():
    final = FinalAnswer.model_validate(VALID)
    assert final.key_numbers[0].value == 94.3


def test_missing_field_is_rejected():
    data = dict(VALID)
    del data["caveat"]
    with pytest.raises(ValidationError):
        FinalAnswer.model_validate(data)


def test_unknown_hub_id_is_rejected():
    data = dict(VALID, hubs=["boston"])
    with pytest.raises(ValidationError):
        FinalAnswer.model_validate(data)


def test_non_numeric_value_is_rejected():
    data = dict(VALID, key_numbers=[{"hub_id": "minneapolis", "label": "winter score", "value": "high"}])
    with pytest.raises(ValidationError):
        FinalAnswer.model_validate(data)
