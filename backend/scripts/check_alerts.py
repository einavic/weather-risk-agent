import json
import os
from pathlib import Path

import httpx

from app.scoring.hub_risk import hub_risk

ROOT = Path(__file__).resolve().parents[2]
HUBS_PATH = ROOT / "data" / "hubs.json"
SNAPSHOT_PATH = ROOT / "data" / "score_snapshot.json"
THRESHOLD = 1.0


def current_scores():
    # {hub_id: {score_name: value}} for all hubs, from the scoring module.
    hubs = json.loads(HUBS_PATH.read_text())
    scores = {}
    for hub in hubs:
        risk = hub_risk(hub["id"])
        scores[hub["id"]] = {**risk["hazards"], "composite": risk["composite"]}
    return scores


def find_alerts(old, new):
    # One alert for every score that moved by THRESHOLD points or more.
    alerts = []
    for hub_id, new_scores in new.items():
        old_scores = old.get(hub_id, {})
        for name, new_value in new_scores.items():
            old_value = old_scores.get(name)
            if old_value is not None and abs(new_value - old_value) >= THRESHOLD:
                alerts.append({"hub_id": hub_id, "score": name, "old": old_value, "new": new_value})
    return alerts


def send_alerts(url, alerts):
    response = httpx.post(url, json={"alerts": alerts}, timeout=30)
    response.raise_for_status()


def save_snapshot(scores):
    SNAPSHOT_PATH.write_text(json.dumps(scores, indent=2) + "\n")


def main():
    new = current_scores()

    if not SNAPSHOT_PATH.exists():
        save_snapshot(new)
        print("snapshot created")
        return

    old = json.loads(SNAPSHOT_PATH.read_text())
    alerts = find_alerts(old, new)

    if alerts:
        print(f"{len(alerts)} alert(s):")
        for alert in alerts:
            print(f"  {alert['hub_id']}: {alert['score']} changed from {alert['old']} to {alert['new']}")
        url = os.environ.get("ALERT_WEBHOOK_URL")
        if url:
            send_alerts(url, alerts)
            print(f"sent to {url}")
    else:
        print("no alerts")

    save_snapshot(new)


if __name__ == "__main__":
    main()
