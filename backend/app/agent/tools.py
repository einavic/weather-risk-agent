import json
from pathlib import Path

from app.data_layer.db import get_connection
from app.scoring.hub_risk import hub_risk
from app.scoring.scoring import CAPS, WEIGHTS

HUBS_PATH = Path(__file__).resolve().parents[3] / "data" / "hubs.json"
HUBS = json.loads(HUBS_PATH.read_text())
HUB_IDS = [hub["id"] for hub in HUBS]
REGIONS = sorted({hub["region"] for hub in HUBS})
SORT_KEYS = ["composite", "hurricane", "flood", "winter", "heat"]
ALLOWED_FIELDS = ["snowfall_cm", "precipitation_mm", "temp_max_c", "temp_min_c", "wind_gust_max_kmh"]
ALLOWED_OPERATORS = [">", ">=", "<", "<=", "="]


def get_hub_risk(hub_ids):
    return {
        "hubs": [hub_risk(hub_id) for hub_id in hub_ids],
        "caps": CAPS,
        "weights": WEIGHTS,
    }


def rank_hubs(region=None, sort_by="composite"):
    rows = []
    for hub in HUBS:
        if region is not None and hub["region"] != region:
            continue
        risk = hub_risk(hub["id"])
        row = {"hub_id": hub["id"], "region": hub["region"]}
        row.update(risk["hazards"])
        row["composite"] = risk["composite"]
        rows.append(row)
    return sorted(rows, key=lambda row: row[sort_by], reverse=True)


def get_weather_stats(hub_id, field, operator, value, start_date, end_date):
    # field and operator are put into the SQL text, so only allow known values.
    if field not in ALLOWED_FIELDS:
        raise ValueError(f"field must be one of {ALLOWED_FIELDS}")
    if operator not in ALLOWED_OPERATORS:
        raise ValueError(f"operator must be one of {ALLOWED_OPERATORS}")

    conn = get_connection()
    total_days, matching_days = conn.execute(
        f"""
        SELECT COUNT(*), SUM({field} {operator} ?)
        FROM daily_weather
        WHERE hub_id = ? AND date BETWEEN ? AND ?
        """,
        (value, hub_id, start_date, end_date),
    ).fetchone()
    conn.close()

    matching_days = matching_days or 0
    percentage = round(matching_days / total_days * 100, 1) if total_days else None
    return {
        "hub_id": hub_id,
        "condition": f"{field} {operator} {value}",
        "start_date": start_date,
        "end_date": end_date,
        "matching_days": matching_days,
        "total_days": total_days,
        "percentage": percentage,
    }


TOOL_FUNCTIONS = {
    "get_hub_risk": get_hub_risk,
    "rank_hubs": rank_hubs,
    "get_weather_stats": get_weather_stats,
}

TOOLS = [
    {
        "name": "get_hub_risk",
        "description": (
            "Get the full risk breakdown for one or more hubs: raw metrics (days per year, "
            "FEMA major disaster counts 2006-2025), normalised metrics (0-100), the four "
            "hazard scores, the composite score, and the caps and weights used."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "hub_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": HUB_IDS},
                    "description": "One or more hub ids.",
                },
            },
            "required": ["hub_ids"],
            "additionalProperties": False,
        },
    },
    {
        "name": "rank_hubs",
        "description": (
            "Rank hubs from highest to lowest by the composite score or by one hazard score. "
            "Optionally limit to one region. Returns the four hazard scores and the composite for each hub."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "enum": REGIONS,
                    "description": "Only include hubs in this region. Leave out for all hubs.",
                },
                "sort_by": {
                    "type": "string",
                    "enum": SORT_KEYS,
                    "description": "Score to sort by. Defaults to composite.",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_weather_stats",
        "description": (
            "Count the days in a date range where a daily weather value meets a condition, "
            "e.g. snowfall_cm > 0 in Denver during 2025. Data covers 2021-01-01 to 2025-12-31. "
            "Units: snowfall cm, precipitation mm, temperatures in °C, wind gusts km/h. "
            "Returns matching_days, total_days and percentage (matching_days as a share of "
            "total_days), so one call answers a 'what percentage of days' question."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "hub_id": {"type": "string", "enum": HUB_IDS},
                "field": {"type": "string", "enum": ALLOWED_FIELDS},
                "operator": {"type": "string", "enum": ALLOWED_OPERATORS},
                "value": {"type": "number"},
                "start_date": {"type": "string", "description": "First day, YYYY-MM-DD."},
                "end_date": {"type": "string", "description": "Last day, YYYY-MM-DD."},
            },
            "required": ["hub_id", "field", "operator", "value", "start_date", "end_date"],
            "additionalProperties": False,
        },
    },
    {
        # No Python function: the agent loop validates this input with FinalAnswer (schema.py).
        "name": "final_answer",
        "description": (
            "Give your final answer to the user. Always finish by calling this tool, "
            "on its own, after any other tools."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "description": "The answer, in plain text."},
                "hubs": {
                    "type": "array",
                    "items": {"type": "string", "enum": HUB_IDS},
                    "description": "The hub ids the answer is about.",
                },
                "key_numbers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "hub_id": {"type": "string", "enum": HUB_IDS},
                            "label": {"type": "string"},
                            "value": {"type": "number"},
                        },
                        "required": ["hub_id", "label", "value"],
                        "additionalProperties": False,
                    },
                    "description": "Main numbers from the answer, each copied from a tool result.",
                },
                "caveat": {"type": "string", "description": "The one caveat that matters most."},
            },
            "required": ["answer", "hubs", "key_numbers", "caveat"],
            "additionalProperties": False,
        },
    },
]
