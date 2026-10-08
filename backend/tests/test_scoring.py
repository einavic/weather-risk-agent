import pytest

from app.scoring.scoring import composite, hazard_scores, is_flood_related, is_hurricane, normalise


def test_normalise_at_zero():
    assert normalise(0, 12) == 0


def test_normalise_at_half_cap():
    assert normalise(6, 12) == 50


def test_normalise_above_cap_is_100():
    assert normalise(30, 12) == 100


def test_normalise_above_cap_returns_float():
    result = normalise(30, 12)
    assert isinstance(result, float)
    assert result == 100.0


def test_hurricane_dr_is_counted():
    assert is_hurricane("Hurricane", "DR")


def test_tropical_storm_dr_is_counted():
    assert is_hurricane("Tropical Storm", "DR")


def test_hurricane_em_is_not_counted():
    assert not is_hurricane("Hurricane", "EM")


def test_flood_dr_is_not_a_hurricane():
    assert not is_hurricane("Flood", "DR")


def test_flood_dr_is_flood_related():
    assert is_flood_related("Flood", "SEVERE STORMS AND FLOODING", "DR")


def test_severe_storm_with_flooding_in_title_is_flood_related():
    assert is_flood_related("Severe Storm", "SEVERE STORMS, TORNADOES, AND FLOODING", "DR")


def test_hurricane_with_flooding_in_title_is_not_flood_related():
    assert not is_flood_related("Hurricane", "HURRICANE IKE AND FLOODING", "DR")


def test_flood_em_is_not_flood_related():
    assert not is_flood_related("Flood", "FLOODING", "EM")


def test_severe_storm_without_flooding_is_not_flood_related():
    assert not is_flood_related("Severe Storm", "SEVERE STORMS AND STRAIGHT-LINE WINDS", "DR")


def test_hazard_scores_average_normalised_metrics():
    raw = {
        "snow_days": 6,
        "ice_days": 60,
        "heavy_rain_days": 10,
        "flood_dr_count": 8,
        "hurricane_dr_count": 2,
        "hot_days": 55,
    }
    assert hazard_scores(raw) == {"hurricane": 50, "flood": 75, "winter": 75, "heat": 100}


def test_composite_all_100_is_100():
    assert composite({"hurricane": 100, "flood": 100, "winter": 100, "heat": 100}) == pytest.approx(100)


def test_composite_uses_weights():
    assert composite({"hurricane": 100, "flood": 0, "winter": 0, "heat": 0}) == pytest.approx(35)
