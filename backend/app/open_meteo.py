import httpx

URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_FIELDS = [
    "snowfall_sum",
    "precipitation_sum",
    "temperature_2m_max",
    "temperature_2m_min",
    "wind_gusts_10m_max",
]


def fetch_daily(lat, lon, start, end):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ",".join(DAILY_FIELDS),
    }
    response = httpx.get(URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def parse_daily(data):
    daily = data["daily"]
    rows = []
    for i, date in enumerate(daily["time"]):
        row = [date] + [daily[field][i] for field in DAILY_FIELDS]
        rows.append(tuple(row))
    return rows
