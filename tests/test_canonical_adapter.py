from __future__ import annotations

import pytest

from q200_engine.ingestion.canonical_adapter import (
    CANONICAL_ADAPTER_VERSION,
    canonical_to_team_stats,
    validated_canonical_to_team_stats,
)

from q200_engine.ingestion.models import (
    CanonicalMatchData,
    MatchInfo,
    StatsHubData,
)

from q200_engine.ingestion.validated_pipeline import (
    map_and_validate,
)


def make_match() -> MatchInfo:
    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="17 Sep 2026",
        time="18:00",
        competition="LaLiga",
        source="StatsHub",
    )


def make_canonical() -> CanonicalMatchData:
    return CanonicalMatchData(
        match=make_match(),
        statshub=StatsHubData(
            match=make_match(),
            values={
                "home_gf_per_match": 1.50,
                "home_ga_per_match": 1.00,
                "away_gf_per_match": 1.20,
                "away_ga_per_match": 1.10,

                "goals_avg": 3.05,
                "xg_avg": 2.92,
                "total_shots_avg": 26.50,
                "shots_on_target_avg": 10.50,
                "possession_avg": 50.85,
                "corners_avg": 9.15,
            },
        ),
        canonical_values={
            "home_gf_per_match": 1.50,
            "home_ga_per_match": 1.00,
            "away_gf_per_match": 1.20,
            "away_ga_per_match": 1.10,

            "goals_avg": 3.05,
            "xg_avg": 2.92,
            "total_shots_avg": 26.50,
            "shots_on_target_avg": 10.50,
            "possession_avg": 50.85,
            "corners_avg": 9.15,
        },
        source_trace={
            "home_gf_per_match": "StatsHub",
            "home_ga_per_match": "StatsHub",
            "away_gf_per_match": "StatsHub",
            "away_ga_per_match": "StatsHub",
        },
    )


def test_adapter_version() -> None:
    assert (
        CANONICAL_ADAPTER_VERSION
        == "Q200-CANONICAL-ADAPTER-V1"
    )


def test_canonical_team_stats_uses_only_explicit_team_rates() -> None:
    stats = canonical_to_team_stats(
        make_canonical()
    )

    assert stats.home_gf == 1.50
    assert stats.home_ga == 1.00
    assert stats.away_gf == 1.20
    assert stats.away_ga == 1.10


def test_general_statshub_averages_are_not_guessed_into_team_stats() -> None:
    stats = canonical_to_team_stats(
        make_canonical()
    )

    assert stats.home_gf != 3.05
    assert stats.away_gf != 3.05


def test_missing_team_rate_is_blocked() -> None:
    canonical = make_canonical()

    values = dict(
        canonical.canonical_values
    )

    del values[
        "away_ga_per_match"
    ]

    broken = CanonicalMatchData(
        match=canonical.match,
        statshub=canonical.statshub,
        canonical_values=values,
        source_trace=canonical.source_trace,
    )

    with pytest.raises(
        ValueError,
        match="away_ga_per_match",
    ):
        canonical_to_team_stats(
            broken
        )


def test_validated_canonical_data_can_enter_team_stats() -> None:
    result = map_and_validate(
        statshub=StatsHubData(
            match=make_match(),
            values={
                "home_gf_per_match": 1.50,
                "home_ga_per_match": 1.00,
                "away_gf_per_match": 1.20,
                "away_ga_per_match": 1.10,

                "goals_avg": 3.05,
                "xg_avg": 2.92,
                "possession_avg": 50.85,
                "corners_avg": 9.15,
            },
        )
    )

    assert result.valid is True

    stats = validated_canonical_to_team_stats(
        result
    )

    assert stats.home_gf == 1.50
    assert stats.home_ga == 1.00
    assert stats.away_gf == 1.20
    assert stats.away_ga == 1.10


def test_invalid_canonical_data_never_reaches_team_stats() -> None:
    result = map_and_validate(
        statshub=StatsHubData(
            match=make_match(),
            values={
                "home_gf_per_match": -1.50,
                "home_ga_per_match": 1.00,
                "away_gf_per_match": 1.20,
                "away_ga_per_match": 1.10,
            },
        )
    )

    assert result.valid is False

    with pytest.raises(
        ValueError,
        match="validation başarısız",
    ):
        validated_canonical_to_team_stats(
            result
        )
