import pytest

from app.agent.tools import get_hub_risk, get_weather_stats, rank_hubs


def test_get_hub_risk_returns_hub_caps_and_weights():
    result = get_hub_risk(["miami"])
    assert len(result["hubs"]) == 1
    assert result["hubs"][0]["hub_id"] == "miami"
    assert result["hubs"][0]["hazards"]["hurricane"] == 100
    assert result["caps"]["hurricane_dr_count"] == 4
    assert result["weights"]["hurricane"] == 0.35


def test_rank_hubs_returns_all_hubs_sorted_by_composite():
    rows = rank_hubs()
    composites = [row["composite"] for row in rows]
    assert len(rows) == 12
    assert composites == sorted(composites, reverse=True)


def test_rank_hubs_filters_by_region():
    rows = rank_hubs(region="West")
    assert sorted(row["hub_id"] for row in rows) == ["denver", "seattle"]


def test_rank_hubs_sorts_by_hazard():
    rows = rank_hubs(sort_by="heat")
    assert rows[0]["hub_id"] == "dallas"


def test_get_weather_stats_denver_snow_2025():
    result = get_weather_stats("denver", "snowfall_cm", ">", 0, "2025-01-01", "2025-12-31")
    assert result["matching_days"] == 37
    assert result["total_days"] == 365
    assert result["percentage"] == 10.1


def test_get_weather_stats_rejects_unknown_field():
    with pytest.raises(ValueError):
        get_weather_stats("denver", "hub_id", ">", 0, "2025-01-01", "2025-12-31")


def test_get_weather_stats_rejects_unknown_operator():
    with pytest.raises(ValueError):
        get_weather_stats("denver", "snowfall_cm", "LIKE", 0, "2025-01-01", "2025-12-31")
