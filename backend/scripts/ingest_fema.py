import json
from pathlib import Path

from app.data_layer.db import get_connection
from app.data_layer.open_fema import fetch_declarations, parse_declarations

HUBS_PATH = Path(__file__).resolve().parents[2] / "data" / "hubs.json"
START = "2006-01-01"
END = "2025-12-31"


def main():
    hubs = json.loads(HUBS_PATH.read_text())
    conn = get_connection()
    for hub in hubs:
        state_fips = hub["county_fips"][:2]
        county_fips = hub["county_fips"][2:]
        data = fetch_declarations(state_fips, county_fips, START, END)
        rows = parse_declarations(data)
        conn.executemany(
            "INSERT OR REPLACE INTO fema_declarations VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(hub["id"],) + row for row in rows],
        )
        conn.commit()
        print(hub["id"], len(rows), "rows")
    conn.close()


if __name__ == "__main__":
    main()
