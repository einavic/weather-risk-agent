YEARS = 5

SNOW_CM = 2.5
ICE_TEMP_MAX_C = 0
HEAVY_RAIN_MM = 25
HOT_TEMP_MAX_C = 35

# Value at which each metric scores 100.
CAPS = {
    "snow_days": 12,
    "ice_days": 60,
    "heavy_rain_days": 20,
    "flood_dr_count": 8,
    "hurricane_dr_count": 4,
    "hot_days": 55,
}

HAZARD_METRICS = {
    "hurricane": ["hurricane_dr_count"],
    "flood": ["heavy_rain_days", "flood_dr_count"],
    "winter": ["snow_days", "ice_days"],
    "heat": ["hot_days"],
}

WEIGHTS = {
    "hurricane": 0.35,
    "flood": 0.25,
    "winter": 0.25,
    "heat": 0.15,
}

HURRICANE_TYPES = ("Hurricane", "Tropical Storm")


def normalise(value, cap):
    return min(value / cap, 1.0) * 100


def is_hurricane(incident_type, declaration_type):
    return incident_type in HURRICANE_TYPES and declaration_type == "DR"


def is_flood_related(incident_type, title, declaration_type):
    if declaration_type != "DR":
        return False
    if incident_type in HURRICANE_TYPES:
        return False
    return incident_type == "Flood" or "flood" in title.lower()


def hazard_scores(raw_metrics):
    scores = {}
    for hazard, metrics in HAZARD_METRICS.items():
        values = [normalise(raw_metrics[m], CAPS[m]) for m in metrics]
        scores[hazard] = sum(values) / len(values)
    return scores


def composite(scores):
    return sum(score * WEIGHTS[hazard] for hazard, score in scores.items())
