from fastapi.testclient import TestClient

import app.main
from app.main import app as api

client = TestClient(api)

FAKE_ANSWER = {
    "answer": "Minneapolis is the most exposed Midwest hub to winter disruption.",
    "hubs": ["minneapolis"],
    "key_numbers": [{"hub_id": "minneapolis", "label": "winter score", "value": 94.3}],
    "caveat": "Scores count how often events happened, not how severe they were.",
}


def use_fake_agent(monkeypatch):
    # Replaces run_agent so no real API call is made. Returns the list of
    # message lists the fake received, one per call.
    calls = []

    def fake_run_agent(messages):
        calls.append(list(messages))
        messages.append({"role": "assistant", "content": "fake reply"})
        return FAKE_ANSWER, messages

    monkeypatch.setattr(app.main, "run_agent", fake_run_agent)
    return calls


def test_first_message_returns_new_session_and_answer(monkeypatch):
    use_fake_agent(monkeypatch)
    response = client.post("/chat", json={"message": "Which Midwest hub is most exposed?", "session_id": None})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["answer"] == FAKE_ANSWER["answer"]
    assert body["hubs"] == ["minneapolis"]
    assert body["key_numbers"] == FAKE_ANSWER["key_numbers"]
    assert body["caveat"] == FAKE_ANSWER["caveat"]


def test_second_message_passes_earlier_history(monkeypatch):
    calls = use_fake_agent(monkeypatch)
    first = client.post("/chat", json={"message": "first question", "session_id": None}).json()
    second = client.post("/chat", json={"message": "second question", "session_id": first["session_id"]}).json()

    assert second["session_id"] == first["session_id"]
    history = calls[1]
    assert [m["content"] for m in history] == ["first question", "fake reply", "second question"]


def test_empty_message_returns_422(monkeypatch):
    use_fake_agent(monkeypatch)
    response = client.post("/chat", json={"message": "", "session_id": None})
    assert response.status_code == 422


def test_agent_error_returns_502(monkeypatch):
    def failing_run_agent(messages):
        raise RuntimeError("Model did not return a valid final answer")

    monkeypatch.setattr(app.main, "run_agent", failing_run_agent)
    response = client.post("/chat", json={"message": "a question", "session_id": None})
    assert response.status_code == 502
    assert response.json()["detail"] == "The agent could not answer this question."
