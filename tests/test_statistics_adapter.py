"""
Q200 Engine - Statistics Adapter Tests

Q200 V3.1
"""

from __future__ import annotations

import pytest

from q200_engine.model import build_model
from q200_engine.schema import TeamStats
from q200_engine.statistics_adapter import (
    adapt_statistics_sources,
    merge_statistics_sources,
)


# =========================================================
# MERGE
# =========================================================

def test_merge_statistics_sources_combines_sources():

    file_1 = {
        "home_gf": 1.80,
        "home_ga": 1.10,
    }

    file_2 = {
        "away_gf": 1.40,
        "away_ga": 1.30,
    }

    merged = merge_statistics_sources(
        file_1,
        file_2,
    )

    assert merged == {
        "home_gf": 1.80,
        "home_ga": 1.10,
        "away_gf": 1.40,
        "away_ga": 1.30,
    }


# =========================================================
# FILE 1 PRIORITY
# =========================================================

def test_file_one_has_priority():

    file_1 = {
        "home_gf": 2.20,
        "home_ga": 1.10,
    }

    file_2 = {
        "home_gf": 1.40,
        "away_gf": 1.30,
    }

    merged = merge_statistics_sources(
        file_1,
        file_2,
    )

    assert merged["home_gf"] == 2.20
    assert merged["home_ga"] == 1.10
    assert merged["away_gf"] == 1.30


# =========================================================
# FILE 2 FILL
# =========================================================

def test_file_two_fills_missing_fields():

    file_1 = {
        "home_gf": 1.80,
        "home_ga": 1.10,
    }

    file_2 = {
        "away_gf": 1.40,
        "away_ga": 1.30,
        "home_xg": 1.75,
    }

    stats = adapt_statistics_sources(
        file_1,
        file_2,
    )

    assert isinstance(
        stats,
        TeamStats,
    )

    assert stats.home_gf == 1.80
    assert stats.home_ga == 1.10
    assert stats.away_gf == 1.40
    assert stats.away_ga == 1.30
    assert stats.home_xg == 1.75


# =========================================================
# TEAM STATS
# =========================================================

def test_adapter_returns_valid_team_stats():

    file_1 = {
        "home_gf": 1.80,
        "home_ga": 1.10,
        "home_xg": 1.75,
        "home_xga": 1.05,
    }

    file_2 = {
        "away_gf": 1.40,
        "away_ga": 1.30,
        "away_xga": 1.25,
        "away_xg": 1.35,
    }

    stats = adapt_statistics_sources(
        file_1,
        file_2,
    )

    assert isinstance(
        stats,
        TeamStats,
    )

    assert stats.home_gf == 1.80
    assert stats.away_gf == 1.40
    assert stats.away_xg == 1.35


# =========================================================
# MODEL INTEGRATION
# =========================================================

def test_adapter_output_can_enter_model():

    file_1 = {
        "home_gf": 1.80,
        "home_ga": 1.10,
    }

    file_2 = {
        "away_gf": 1.40,
        "away_ga": 1.30,
    }

    stats = adapt_statistics_sources(
        file_1,
        file_2,
    )

    snapshot = build_model(
        stats
    )

    assert snapshot.locked is True
    assert snapshot.lambda_home > 0
    assert snapshot.lambda_away > 0


# =========================================================
# FIELD NORMALIZATION
# =========================================================

def test_adapter_normalizes_field_names():

    file_1 = {
        " HOME_GF ": "1.80",
        "HOME_GA": "1.10",
    }

    file_2 = {
        "Away_GF": "1.40",
        "away_ga": "1.30",
    }

    stats = adapt_statistics_sources(
        file_1,
        file_2,
    )

    assert stats.home_gf == 1.80
    assert stats.home_ga == 1.10
    assert stats.away_gf == 1.40
    assert stats.away_ga == 1.30


# =========================================================
# UNKNOWN FIELD
# =========================================================

def test_unknown_field_is_rejected():

    file_1 = {
        "home_gf": 1.80,
        "unknown": 10,
    }

    file_2 = {
        "away_gf": 1.40,
    }

    with pytest.raises(ValueError):

        merge_statistics_sources(
            file_1,
            file_2,
        )


# =========================================================
# MISSING REQUIRED FIELDS
# =========================================================

def test_missing_required_fields_are_rejected_after_merge():

    file_1 = {
        "home_gf": 1.80,
    }

    file_2 = {
        "home_ga": 1.10,
    }

    with pytest.raises(ValueError):

        adapt_statistics_sources(
            file_1,
            file_2,
        )


# =========================================================
# INVALID SOURCE
# =========================================================

def test_non_mapping_source_is_rejected():

    with pytest.raises(TypeError):

        merge_statistics_sources(
            [],
            {
                "away_gf": 1.40,
            },
        )


# =========================================================
# NO MUTATION
# =========================================================

def test_sources_are_not_mutated():

    file_1 = {
        "home_gf": 1.80,
        "home_ga": 1.10,
    }

    file_2 = {
        "away_gf": 1.40,
        "away_ga": 1.30,
    }

    original_file_1 = dict(
        file_1
    )

    original_file_2 = dict(
        file_2
    )

    merge_statistics_sources(
        file_1,
        file_2,
    )

    assert file_1 == original_file_1
    assert file_2 == original_file_2
