"""
Q200 Engine - Input Validation Tests

Q200 V3.1
"""

from __future__ import annotations

import math

import pytest

from q200_engine.input_validation import (
    build_team_stats,
    normalize_statistics,
    validate_statistics,
    validate_team_stats,
)
from q200_engine.schema import TeamStats


# =========================================================
# VALID INPUT
# =========================================================

def test_build_team_stats():
    data = {
        "home_gf": 1.80,
        "home_ga": 1.10,
        "away_gf": 1.40,
        "away_ga": 1.30,
        "home_xg": 1.75,
        "home_xga": 1.05,
        "away_xga": 1.25,
        "away_xg": 1.35,
    }

    stats = build_team_stats(data)

    assert isinstance(
        stats,
        TeamStats,
    )

    assert stats.home_gf == 1.80
    assert stats.home_ga == 1.10
    assert stats.away_gf == 1.40
    assert stats.away_ga == 1.30

    assert stats.home_xg == 1.75
    assert stats.home_xga == 1.05
    assert stats.away_xga == 1.25
    assert stats.away_xg == 1.35


# =========================================================
# STRING NUMBER NORMALIZATION
# =========================================================

def test_numeric_strings_are_converted():
    data = {
        "home_gf": "1.80",
        "home_ga": "1.10",
        "away_gf": "1.40",
        "away_ga": "1.30",
        "home_xg": "1.75",
    }

    stats = build_team_stats(data)

    assert isinstance(
        stats.home_gf,
        float,
    )

    assert isinstance(
        stats.home_ga,
        float,
    )

    assert math.isclose(
        stats.home_gf,
        1.80,
    )

    assert math.isclose(
        stats.home_xg,
        1.75,
    )


# =========================================================
# CASE NORMALIZATION
# =========================================================

def test_field_names_are_normalized():
    data = {
        " HOME_GF ": 1.80,
        "HOME_GA": 1.10,
        "Away_GF": 1.40,
        "away_ga": 1.30,
    }

    stats = build_team_stats(data)

    assert stats.home_gf == 1.80
    assert stats.home_ga == 1.10
    assert stats.away_gf == 1.40
    assert stats.away_ga == 1.30


# =========================================================
# OPTIONAL DATA
# =========================================================

def test_optional_xg_fields_can_be_missing():
    data = {
        "home_gf": 1.80,
        "home_ga": 1.10,
        "away_gf": 1.40,
        "away_ga": 1.30,
    }

    stats = build_team_stats(data)

    assert stats.home_xg is None
    assert stats.home_xga is None
    assert stats.away_xga is None
    assert stats.away_xg is None


# =========================================================
# DEFAULT AWAY GA
# =========================================================

def test_away_ga_defaults_to_zero():
    data = {
        "home_gf": 1.80,
        "home_ga": 1.10,
        "away_gf": 1.40,
    }

    stats = build_team_stats(data)

    assert stats.away_ga == 0.0


# =========================================================
# MISSING REQUIRED FIELD
# =========================================================

def test_missing_required_field():
    data = {
        "home_gf": 1.80,
        "home_ga": 1.10,
    }

    with pytest.raises(ValueError):
        build_team_stats(data)


# =========================================================
# NEGATIVE VALUE
# =========================================================

def test_negative_value_is_rejected():
    data = {
        "home_gf": -1.80,
        "home_ga": 1.10,
        "away_gf": 1.40,
    }

    with pytest.raises(ValueError):
        build_team_stats(data)


# =========================================================
# INVALID STRING
# =========================================================

def test_invalid_string_is_rejected():
    data = {
        "home_gf": "abc",
        "home_ga": 1.10,
        "away_gf": 1.40,
    }

    with pytest.raises(ValueError):
        build_team_stats(data)


# =========================================================
# NAN
# =========================================================

def test_nan_is_rejected():
    data = {
        "home_gf": float("nan"),
        "home_ga": 1.10,
        "away_gf": 1.40,
    }

    with pytest.raises(ValueError):
        build_team_stats(data)


# =========================================================
# INFINITY
# =========================================================

def test_infinity_is_rejected():
    data = {
        "home_gf": float("inf"),
        "home_ga": 1.10,
        "away_gf": 1.40,
    }

    with pytest.raises(ValueError):
        build_team_stats(data)


# =========================================================
# BOOLEAN
# =========================================================

def test_boolean_is_rejected():
    data = {
        "home_gf": True,
        "home_ga": 1.10,
        "away_gf": 1.40,
    }

    with pytest.raises(ValueError):
        build_team_stats(data)


# =========================================================
# UNKNOWN FIELD
# =========================================================

def test_unknown_field_is_rejected():
    data = {
        "home_gf": 1.80,
        "home_ga": 1.10,
        "away_gf": 1.40,
        "unknown_field": 10,
    }

    with pytest.raises(ValueError):
        build_team_stats(data)


# =========================================================
# NORMALIZE ONLY
# =========================================================

def test_normalize_statistics():
    data = {
        " HOME_GF ": 1.80,
        "HOME_GA": 1.10,
        "Away_GF": 1.40,
    }

    normalized = normalize_statistics(
        data
    )

    assert "home_gf" in normalized
    assert "home_ga" in normalized
    assert "away_gf" in normalized


# =========================================================
# INVALID INPUT TYPE
# =========================================================

def test_non_mapping_input():
    with pytest.raises(TypeError):
        build_team_stats(
            ["home_gf", 1.80]
        )


# =========================================================
# VALIDATE EXISTING TEAM STATS
# =========================================================

def test_validate_existing_team_stats():
    stats = TeamStats(
        home_gf=1.80,
        home_ga=1.10,
        away_gf=1.40,
        away_ga=1.30,
        home_xg=1.75,
        home_xga=1.05,
        away_xga=1.25,
        away_xg=1.35,
    )

    validated = validate_team_stats(
        stats
    )

    assert validated is stats


# =========================================================
# INVALID TEAM STATS TYPE
# =========================================================

def test_validate_team_stats_rejects_wrong_type():
    with pytest.raises(TypeError):
        validate_team_stats(
            {
                "home_gf": 1.80
            }
        )


# =========================================================
# PUBLIC VALIDATION FLOW
# =========================================================

def test_validate_statistics_full_flow():
    data = {
        "home_gf": 1.80,
        "home_ga": 1.10,
        "away_gf": 1.40,
        "away_ga": 1.30,
        "home_xg": 1.75,
        "home_xga": 1.05,
        "away_xga": 1.25,
        "away_xg": 1.35,
    }

    stats = validate_statistics(
        data
    )

    assert isinstance(
        stats,
        TeamStats,
    )

    assert stats.home_gf == 1.80
    assert stats.away_xg == 1.35
