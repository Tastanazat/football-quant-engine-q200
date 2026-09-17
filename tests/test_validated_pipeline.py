from __future__ import annotations

import pytest

from q200_engine.ingestion.models import (
    GoalStats,
    MatchInfo,
    SoccerStatsData,
    StatsHubData,
)

from q200_engine.ingestion.validated_pipeline import (
    VALIDATED_INGESTION_VERSION,
    ValidatedCanonicalData,
    map_and_validate,
    require_valid,
    validated_pipeline_to_dict,
)


REQUIRED = (
    "home_gf_per_match",
    "home_ga_per_match",
    "away_gf_per_match",
    "away_ga_per_match",
)


def make_match() -> MatchInfo:
    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="17 Sep 2026",
        time="18:00",
        competition="LaLiga",
        source="SoccerSTATS",
    )


def make_soccerstats() -> SoccerStatsData:
    return SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            home_gf=2.0,
            home_ga=0.0,
            away_gf=0.0,
            away_ga=4.0,
            home_gf_per_match=1.0,
            home_ga_per_match=0.0,
            away_gf_per_match=0.0,
            away_ga_per_match=2.0,
            home_scoring_rate=100.0,
            away_scoring_rate=0.0,
        ),
    )


def test_pipeline_version():
    assert (
        VALIDATED_INGESTION_VERSION
        == "Q200-VALIDATED-INGESTION-V1"
    )


def test_map_and_validate_valid_soccerstats():
    result = map_and_validate(
        soccerstats=make_soccerstats(),
        required_fields=REQUIRED,
    )

    assert isinstance(
        result,
        ValidatedCanonicalData,
    )

    assert result.valid is True

    assert (
        result.canonical.match.home_team
        == "Real Betis"
    )

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.0
    )

    assert (
        result.source_trace[
            "home_gf_per_match"
        ]
        == "SoccerSTATS"
    )

    assert result.validation.error_count == 0


def test_invalid_canonical_data_is_reported():
    soccerstats = SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            home_gf_per_match=-1.0,
            home_ga_per_match=1.0,
            away_gf_per_match=1.0,
            away_ga_per_match=1.0,
        ),
    )

    result = map_and_validate(
        soccerstats=soccerstats,
        required_fields=REQUIRED,
    )

    assert result.valid is False
    assert result.validation.error_count == 1

    assert (
        result.validation.issues[0].code
        == "NEGATIVE"
    )


def test_missing_required_data_is_invalid():
    soccerstats = SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            home_gf_per_match=1.0,
            home_ga_per_match=1.0,
            away_gf_per_match=1.0,
        ),
    )

    result = map_and_validate(
        soccerstats=soccerstats,
        required_fields=REQUIRED,
    )

    assert result.valid is False

    assert (
        "away_ga_per_match"
        in result.validation.missing_fields
    )


def test_require_valid_returns_canonical_data():
    result = map_and_validate(
        soccerstats=make_soccerstats(),
        required_fields=REQUIRED,
    )

    canonical = require_valid(result)

    assert canonical.match.home_team == (
        "Real Betis"
    )

    assert (
        canonical.canonical_values[
            "away_gf_per_match"
        ]
        == 0.0
    )


def test_require_valid_blocks_invalid_data():
    soccerstats = SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            home_gf_per_match=-2.0,
            home_ga_per_match=1.0,
            away_gf_per_match=1.0,
            away_ga_per_match=1.0,
        ),
    )

    result = map_and_validate(
        soccerstats=soccerstats,
        required_fields=REQUIRED,
    )

    assert result.valid is False

    with pytest.raises(
        ValueError,
        match="validation başarısız",
    ):
        require_valid(result)


def test_statshub_only_can_be_validated():
    statshub = StatsHubData(
        match=make_match(),
        values={
            "home_gf_per_match": 1.5,
            "home_ga_per_match": 1.0,
            "away_gf_per_match": 1.2,
            "away_ga_per_match": 1.1,
            "possession": 55.0,
            "total_shots_avg": 26.5,
            "corners_avg": 9.0,
        },
    )

    result = map_and_validate(
        statshub=statshub,
        required_fields=REQUIRED,
    )

    assert result.valid is True

    assert (
        result.canonical_values[
            "possession"
        ]
        == 55.0
    )

    assert (
        result.source_trace[
            "possession"
        ]
        == "StatsHub"
    )


def test_soccerstats_priority_remains_intact():
    soccerstats = make_soccerstats()

    statshub = StatsHubData(
        match=make_match(),
        values={
            "home_gf_per_match": 99.0,
            "possession": 55.0,
        },
    )

    result = map_and_validate(
        soccerstats=soccerstats,
        statshub=statshub,
        required_fields=REQUIRED,
    )

    assert result.valid is True

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.0
    )

    assert (
        result.source_trace[
            "home_gf_per_match"
        ]
        == "SoccerSTATS"
    )

    assert (
        result.canonical_values[
            "possession"
        ]
        == 55.0
    )

    assert (
        result.source_trace[
            "possession"
        ]
        == "StatsHub"
    )

    assert result.warnings


def test_invalid_source_combination_raises():
    with pytest.raises(
        ValueError,
        match="En az bir",
    ):
        map_and_validate(
            required_fields=REQUIRED,
        )


def test_required_fields_must_be_tuple():
    with pytest.raises(TypeError):
        map_and_validate(
            soccerstats=make_soccerstats(),
            required_fields=[
                "home_gf_per_match",
            ],
        )


def test_serialization_contains_validation():
    result = map_and_validate(
        soccerstats=make_soccerstats(),
        required_fields=REQUIRED,
    )

    payload = validated_pipeline_to_dict(
        result
    )

    assert (
        payload["pipeline_version"]
        == VALIDATED_INGESTION_VERSION
    )

    assert payload["valid"] is True

    assert (
        payload["canonical"][
            "canonical_values"
        ]["home_gf_per_match"]
        == 1.0
    )

    assert (
        payload["validation"]["valid"]
        is True
    )


def test_serialization_contains_errors():
    soccerstats = SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            home_gf_per_match=-1.0,
            home_ga_per_match=1.0,
            away_gf_per_match=1.0,
            away_ga_per_match=1.0,
        ),
    )

    result = map_and_validate(
        soccerstats=soccerstats,
        required_fields=REQUIRED,
    )

    payload = validated_pipeline_to_dict(
        result
    )

    assert payload["valid"] is False

    assert (
        payload["validation"]["issues"][0][
            "code"
        ]
        == "NEGATIVE"
    )


def test_wrong_result_type_is_rejected():
    with pytest.raises(TypeError):
        require_valid({})  # type: ignore[arg-type]


def test_wrong_serialization_type_is_rejected():
    with pytest.raises(TypeError):
        validated_pipeline_to_dict(
            {}  # type: ignore[arg-type]
        )
