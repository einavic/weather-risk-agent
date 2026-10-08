import json
from pathlib import Path

from app.db import get_connection

HUBS_PATH = Path(__file__).resolve().parents[2] / "data" / "hubs.json"
YEARS = 5.0


def format_value(value):
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def print_line(cells, widths):
    # First two columns (hub, region) are left-aligned text; the rest are right-aligned numbers.
    line = cells[0].ljust(widths[0]) + cells[1].ljust(widths[1])
    for cell, width in zip(cells[2:], widths[2:]):
        line += cell.rjust(width)
    print(line)


def print_table(title, headers, rows):
    lines = [[format_value(v) for v in row] for row in rows]
    widths = []
    for i, header in enumerate(headers):
        widest = max([len(header)] + [len(line[i]) for line in lines])
        widths.append(widest + 2)
    print()
    print(title)
    print_line(headers, widths)
    for line in lines:
        print_line(line, widths)
    for label, func in [("min", min), ("max", max)]:
        cells = [label, ""]
        for i in range(2, len(headers)):
            cells.append(format_value(func(row[i] for row in rows)))
        print_line(cells, widths)


def weather_rows(conn, hubs, select_sql):
    results = {}
    for row in conn.execute(f"SELECT hub_id, {select_sql} FROM daily_weather GROUP BY hub_id"):
        results[row[0]] = row[1:]
    return [(hub["id"], hub["region"]) + tuple(results[hub["id"]]) for hub in hubs]


def main():
    hubs = json.loads(HUBS_PATH.read_text())
    hubs.sort(key=lambda hub: (hub["region"], hub["id"]))
    conn = get_connection()

    rows = weather_rows(
        conn,
        hubs,
        f"""SUM(snowfall_cm > 0) / {YEARS},
            SUM(snowfall_cm >= 2.5) / {YEARS},
            SUM(snowfall_cm >= 10) / {YEARS},
            SUM(temp_min_c <= 0) / {YEARS},
            SUM(temp_max_c <= 0) / {YEARS}""",
    )
    print_table(
        "WINTER (avg days/year, 2021-2025)",
        ["hub", "region", "snow>0", "snow>=2.5", "snow>=10", "tmin<=0", "tmax<=0"],
        rows,
    )

    rows = weather_rows(
        conn,
        hubs,
        f"""SUM(precipitation_mm >= 25) / {YEARS},
            SUM(precipitation_mm >= 50) / {YEARS},
            SUM(precipitation_mm >= 100) / {YEARS}""",
    )
    print_table(
        "HEAVY RAIN (avg days/year, 2021-2025)",
        ["hub", "region", "precip>=25", "precip>=50", "precip>=100"],
        rows,
    )

    rows = weather_rows(
        conn,
        hubs,
        f"""SUM(wind_gust_max_kmh >= 60) / {YEARS},
            SUM(wind_gust_max_kmh >= 75) / {YEARS},
            SUM(wind_gust_max_kmh >= 90) / {YEARS},
            MAX(wind_gust_max_kmh)""",
    )
    print_table(
        "WIND (avg days/year, 2021-2025; max_gust = highest single day in km/h)",
        ["hub", "region", "gust>=60", "gust>=75", "gust>=90", "max_gust"],
        rows,
    )

    rows = weather_rows(
        conn,
        hubs,
        f"""SUM(temp_max_c >= 32) / {YEARS},
            SUM(temp_max_c >= 35) / {YEARS},
            SUM(temp_max_c >= 38) / {YEARS}""",
    )
    print_table(
        "HEAT (avg days/year, 2021-2025)",
        ["hub", "region", "tmax>=32", "tmax>=35", "tmax>=38"],
        rows,
    )

    counts = {}
    for hub_id, incident_type, count in conn.execute(
        "SELECT hub_id, incident_type, COUNT(*) FROM fema_declarations GROUP BY hub_id, incident_type"
    ):
        counts[(hub_id, incident_type)] = count
    types = sorted({incident_type for _, incident_type in counts})
    rows = [
        (hub["id"], hub["region"]) + tuple(counts.get((hub["id"], t), 0) for t in types)
        for hub in hubs
    ]
    print_table(
        "FEMA (total declarations, 2006-2025)",
        ["hub", "region"] + types,
        rows,
    )

    conn.close()


if __name__ == "__main__":
    main()
