import json
from pathlib import Path

from app.data_layer.open_fema import parse_declarations

SAMPLE_PATH = Path(__file__).parent / "open_fema_sample.json"


def test_parse_declarations_returns_one_row_per_record():
    data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    rows = parse_declarations(data)
    assert len(rows) == 2
    assert rows[0] == (4498, "Biological", "2020-03-28", "COVID-19 PANDEMIC", "Denver (County)", "DR")
    assert rows[1][2] == "2015-07-16"
