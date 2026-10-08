import json
from pathlib import Path

from app.open_meteo import parse_daily

SAMPLE_PATH = Path(__file__).parent / "open_meteo_sample.json"


def test_parse_daily_returns_one_row_per_day():
    data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    rows = parse_daily(data)
    assert len(rows) == 3
    assert rows[0] == ("2025-01-01", 0.0, 0.0, 3.4, -7.4, 17.6)
    assert rows[2] == ("2025-01-03", 0.0, 0.0, 8.1, -4.4, 17.6)
