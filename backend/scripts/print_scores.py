import json
from pathlib import Path

from app.hub_risk import hub_risk

HUBS_PATH = Path(__file__).resolve().parents[2] / "data" / "hubs.json"
HAZARDS = ["hurricane", "flood", "winter", "heat"]


def main():
    hubs = json.loads(HUBS_PATH.read_text())
    hubs.sort(key=lambda hub: (hub["region"], hub["id"]))
    print(f"{'hub':14}{'region':9}" + "".join(f"{h:>11}" for h in HAZARDS) + f"{'composite':>11}")
    for hub in hubs:
        risk = hub_risk(hub["id"])
        scores = "".join(f"{risk['hazards'][h]:>11.1f}" for h in HAZARDS)
        print(f"{hub['id']:14}{hub['region']:9}{scores}{risk['composite']:>11.1f}")


if __name__ == "__main__":
    main()
