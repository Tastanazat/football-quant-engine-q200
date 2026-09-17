from __future__ import annotations

import pytest

from q200_engine.data_review import (
    approve_review,
    update_review_field,
)

from q200_engine.ingestion.models import (
    MatchInfo,
    StatsHubData,
)

from q200_engine.statshub_feature_adapter import (
    STATSHUB_FEATURE_ADAPTER_VERSION,
    build_features_from_approved_reviews,
    build_features_from_statshub_pair,
    statshub_pair_to_feature_input,
)

from q200_engine.statshub_ocr import (
    create_statshub_review,
)


STATSHUB_HOME_TEXT = """
Goals 3.05 1.70 1.35
Corners 9.15 4.30 4.85
Expected Goals (xG) 2.92 1.50 1.42
Shots On Target 10.50 5.65 4.85
Shots In The Box 15.00 8.00 7.00
Total Shots 26.50 15.05 11.45
Shots Outside The Box 11.50 7.05 4.45
Possession 100.00 50.85 49.15
Big Chance Created 8.00 5.00 3.00
Big Chance Scored 4.00 3.00 1.00
Big Chance Missed 4.00 2.00 2.00
Passes 983.85 498.85 485.00
Touches In Opp Box 40.00 25.00 15.00
"""


STATSHUB_AWAY_TEXT = """
Goals 2.10 1.20 0.90
Corners 8.00 3.00 5.00
Expected Goals (xG) 2.30 1.10 1.20
Shots On Target 8.00 4.00 4.00
Shots In The Box 12.00 6.00 6.00
Total Shots 22.00 12.00 10.00
Shots Outside The Box 10.00 6.00 4.00
Possession 100.00 45.00 55.00
Big Chance Created 5.00 3.00 2.00
Big Chance Scored 2.00 1.00 1.00
Big Chance Missed 3.00 2.00 1.00
Passes 850.00 400.00 450.00
Touches In Opp Box 30.00 18.00 12.00
"""


def match() -> MatchInfo:
    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="17 Sep 2026",
        time="18:00",
        competition="LaLiga",
        source="StatsHub",
    )


def review(
    text: str,
    file_name: str,
):
    return create_statshub_review(
        file_name,
        ocr_text=text,
    )


# =========================================================
# VERSION
# =========================================================

def test_adapter_version() -> None:
    assert (
        STATSHUB_FEATURE_ADAPTER_VERSION
        == "Q200-STATSHUB-FEATURE-ADAPTER-V1"
    )


# =========================================================
# HOME / AWAY MAPPING
# =========================================================

def test_pair_uses_for_values_and_preserves_home_away_direction() -> None:
    home = StatsHubData(
        match=match(),
        values={
            "xg_avg": 2.92,
            "xg_for": 1.50,
            "xg_agt": 1.42,
            "corners_for": 4.30,
            "possession_for": 50.85,
        },
    )

    away = StatsHubData(
        match=match(),
        values={
            "xg_avg": 2.30,
            "xg_for": 1.10,
            "xg_agt": 1.20,
            "corners_for": 3.00,
            "possession_for": 45.00,
        },
    )

    result = (
        statshub_pair_to_feature_input(
            home,
            away,
        )
    )

    assert result[
        "home_xg"
    ] == 1.50

    assert result[
        "away_xg"
    ] == 1.10

    assert result[
        "home_corners"
    ] == 4.30

    assert result[
        "away_corners"
    ] == 3.00

    assert result[
        "home_possession"
    ] == 50.85

    assert result[
        "away_possession"
    ] == 45.00

    assert (
        "home_xg_avg"
        not in result
    )

    assert (
        "away_xg_avg"
        not in result
    )

    assert (
        "home_xg_agt"
        not in result
    )

    assert (
        "away_xg_agt"
        not in result
    )


# =========================================================
# FEATURE ENGINE
# =========================================================

def test_build_features_from_statshub_pair() -> None:
    home = StatsHubData(
        match=match(),
        values={
            "total_shots_for": 15.05,
            "shots_on_target_for": 5.65,
            "shots_in_box_for": 8.00,
            "shots_outside_box_for": 7.05,
            "xg_for": 1.50,
            "possession_for": 50.85,
            "corners_for": 4.30,
            "big_chance_created_for": 5.00,
            "big_chance_scored_for": 3.00,
            "big_chance_missed_for": 2.00,
        },
    )

    away = StatsHubData(
        match=match(),
        values={
            "total_shots_for": 12.00,
            "shots_on_target_for": 4.00,
            "shots_in_box_for": 6.00,
            "shots_outside_box_for": 6.00,
            "xg_for": 1.10,
            "possession_for": 45.00,
            "corners_for": 3.00,
            "big_chance_created_for": 3.00,
            "big_chance_scored_for": 1.00,
            "big_chance_missed_for": 2.00,
        },
    )

    features = (
        build_features_from_statshub_pair(
            home,
            away,
        )
    )

    assert (
        features.home_total_shots
        == 15.05
    )

    assert (
        features.away_total_shots
        == 12.00
    )

    assert (
        features.home_xg
        == 1.50
    )

    assert (
        features.away_xg
        == 1.10
    )

    assert (
        features.home_possession
        == 50.85
    )

    assert (
        features.away_possession
        == 45.00
    )

    assert (
        features.home_corners
        == 4.30
    )

    assert (
        features.away_corners
        == 3.00
    )

    assert (
        features.home_big_chance_created
        == 5.00
    )

    assert (
        features.away_big_chance_created
        == 3.00
    )


# =========================================================
# APPROVAL GATE
# =========================================================

def test_unapproved_reviews_are_blocked() -> None:
    home = review(
        STATSHUB_HOME_TEXT,
        "betis.jpg",
    )

    away = review(
        STATSHUB_AWAY_TEXT,
        "getafe.jpg",
    )

    approve_review(home)

    with pytest.raises(
        RuntimeError,
        match="onaylanmalıdır",
    ):
        build_features_from_approved_reviews(
            home,
            away,
            match=match(),
        )


# =========================================================
# APPROVED REVIEWS
# =========================================================

def test_approved_reviews_build_features() -> None:
    home = review(
        STATSHUB_HOME_TEXT,
        "betis.jpg",
    )

    away = review(
        STATSHUB_AWAY_TEXT,
        "getafe.jpg",
    )

    approve_review(home)
    approve_review(away)

    features = (
        build_features_from_approved_reviews(
            home,
            away,
            match=match(),
        )
    )

    assert (
        features.home_xg
        == 1.50
    )

    assert (
        features.away_xg
        == 1.10
    )

    assert (
        features.home_total_shots
        == 15.05
    )

    assert (
        features.away_total_shots
        == 12.00
    )

    assert (
        features.home_corners
        == 4.30
    )

    assert (
        features.away_corners
        == 3.00
    )

    assert (
        features.home_possession
        == 50.85
    )

    assert (
        features.away_possession
        == 45.00
    )


# =========================================================
# MANUAL CORRECTION
# =========================================================

def test_manual_correction_reaches_feature_engine_but_raw_value_remains() -> None:
    home = review(
        STATSHUB_HOME_TEXT,
        "betis.jpg",
    )

    away = review(
        STATSHUB_AWAY_TEXT,
        "getafe.jpg",
    )

    update_review_field(
        home,
        "corners_for",
        4.00,
        note="OCR düzeltmesi",
    )

    approve_review(home)
    approve_review(away)

    features = (
        build_features_from_approved_reviews(
            home,
            away,
            match=match(),
        )
    )

    assert (
        features.home_corners
        == 4.00
    )

    assert (
        home.raw_values()[
            "corners_for"
        ]
        == 4.30
    )

    assert (
        home.fields[
            "corners_for"
        ].status
        == "MANUAL"
    )


# =========================================================
# AVG / AGT PROTECTION
# =========================================================

def test_avg_and_agt_are_not_used_as_home_or_away_values() -> None:
    home = StatsHubData(
        match=match(),
        values={
            "xg_avg": 99.0,
            "xg_for": 1.50,
            "xg_agt": 77.0,
        },
    )

    away = StatsHubData(
        match=match(),
        values={
            "xg_avg": 88.0,
            "xg_for": 1.10,
            "xg_agt": 66.0,
        },
    )

    features = (
        build_features_from_statshub_pair(
            home,
            away,
        )
    )

    assert (
        features.home_xg
        == 1.50
    )

    assert (
        features.away_xg
        == 1.10
    )

    assert (
        features.home_xg
        != 99.0
    )

    assert (
        features.away_xg
        != 88.0
    )


# =========================================================
# VALIDATION
# =========================================================

def test_invalid_statshub_data_is_rejected_by_feature_engine() -> None:
    home = StatsHubData(
        match=match(),
        values={
            "possession_for": 150.0,
        },
    )

    away = StatsHubData(
        match=match(),
        values={
            "possession_for": 45.0,
        },
    )

    with pytest.raises(
        ValueError,
        match="100",
    ):
        build_features_from_statshub_pair(
            home,
            away,
        )


# =========================================================
# TYPE VALIDATION
# =========================================================

def test_invalid_home_type_is_rejected() -> None:
    away = StatsHubData(
        match=match(),
        values={
            "xg_for": 1.10,
        },
    )

    with pytest.raises(
        TypeError,
        match="home StatsHubData",
    ):
        statshub_pair_to_feature_input(
            {},
            away,
        )


def test_invalid_away_type_is_rejected() -> None:
    home = StatsHubData(
        match=match(),
        values={
            "xg_for": 1.50,
        },
    )

    with pytest.raises(
        TypeError,
        match="away StatsHubData",
    ):
        statshub_pair_to_feature_input(
            home,
            {},
        )
