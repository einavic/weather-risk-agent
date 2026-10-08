from app.data_layer.db import get_connection
from app.scoring.scoring import (
    CAPS,
    HEAVY_RAIN_MM,
    HOT_TEMP_MAX_C,
    ICE_TEMP_MAX_C,
    SNOW_CM,
    YEARS,
    composite,
    hazard_scores,
    is_flood_related,
    is_hurricane,
    normalise,
)


def read_raw_metrics(hub_id):
    conn = get_connection()
    snow, ice, rain, hot = conn.execute(
        """
        SELECT SUM(snowfall_cm >= ?),
               SUM(temp_max_c <= ?),
               SUM(precipitation_mm >= ?),
               SUM(temp_max_c >= ?)
        FROM daily_weather
        WHERE hub_id = ?
        """,
        (SNOW_CM, ICE_TEMP_MAX_C, HEAVY_RAIN_MM, HOT_TEMP_MAX_C, hub_id),
    ).fetchone()
    declarations = conn.execute(
        "SELECT incident_type, title, declaration_type FROM fema_declarations WHERE hub_id = ?",
        (hub_id,),
    ).fetchall()
    conn.close()

    hurricane_count = 0
    flood_count = 0
    for incident_type, title, declaration_type in declarations:
        if is_hurricane(incident_type, declaration_type):
            hurricane_count += 1
        if is_flood_related(incident_type, title, declaration_type):
            flood_count += 1

    return {
        "snow_days": snow / YEARS,
        "ice_days": ice / YEARS,
        "heavy_rain_days": rain / YEARS,
        "flood_dr_count": flood_count,
        "hurricane_dr_count": hurricane_count,
        "hot_days": hot / YEARS,
    }


def round_values(values):
    return {key: round(value, 1) for key, value in values.items()}


def hub_risk(hub_id):
    raw = read_raw_metrics(hub_id)
    normalised = {metric: normalise(value, CAPS[metric]) for metric, value in raw.items()}
    hazards = hazard_scores(raw)
    return {
        "hub_id": hub_id,
        "raw": round_values(raw),
        "normalised": round_values(normalised),
        "hazards": round_values(hazards),
        "composite": round(composite(hazards), 1),
    }
