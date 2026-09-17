from __future__ import annotations

import pytest

from q200_engine.ingestion.canonical_adapter import (
    CANONICAL_ADAPTER_VERSION,
    canonical_to_team_stats,
    validated_canonical_to_team_stats,
)
from q200_engine.ingestion.models import (
    GoalStats,
    MatchInfo,
    SoccerStatsData,
    StatsHubData,
)
from q200_engine.ingestion.validated_pipeline import (
    map_and_validate,
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
            home_gf_per_match=1.50,
            home_ga_per_match=1.00,
            away_gf_per_match=1.20,
            away_ga_per_match=1.10,
        ),
    )


def test_adapter_version() -> None:
    assert (
        CANONICAL_ADAPTER_VERSION
        == "Q200-CANONICAL-ADAPTER-V1"
    )


def test_canonical_team_stats_uses_explicit_team_rates() -> None:
    result = map_and_validate(
        soccerstats=make_soccerstats(),
        required_fields=REQUIRED,
    )

    stats = canonical_to_team_stats(
        result.canonical
    )

    assert stats.home_gf == 1.50
    assert stats.home_ga == 1.00
    assert stats.away_gf == 1.20
    assert stats.away_ga == 1.10


def test_general_statshub_averages_are_not_guessed_into_team_stats() -> None:
    canonical_result = map_and_validate(
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
        required_fields=REQUIRED,
    )

    stats = canonical_to_team_stats(
        canonical_result.canonical
    )

    assert stats.home_gf == 1.50
    assert stats.away_gf == 1.20
    assert stats.home_gf != 3.05
    assert stats.away_gf != 3.05


def test_explicit_xg_fields_are_transferred() -> None:
    soccerstats = make_soccerstats()

    canonical = map_and_validate(
        soccerstats=soccerstats,
        statshub=StatsHubData(
            match=make_match(),
            values={
                "home_xg": 1.70,
                "home_xga": 0.95,
                "away_xg": 1.20,
                "away_xga": 1.35,
            },
        ),
        required_fields=REQUIRED,
    ).canonical

    stats = canonical_to_team_stats(canonical)

    assert stats.home_xg == 1.70
    assert stats.home_xga == 0.95
    assert stats.away_xg == 1.20
    assert stats.away_xga == 1.35


def test_missing_required_canonical_field_is_blocked() -> None:
    canonical = map_and_validate(
        soccerstats=make_soccerstats(),
        required_fields=REQUIRED,
    ).canonical

    values = dict(canonical.canonical_values)
    del values["away_ga_per_match"]

    broken = type(canonical)(
        match=canonical.match,
        soccerstats=canonical.soccerstats,
        statshub=canonical.statshub,
        odds=canonical.odds,
        canonical_values=values,
        source_trace=canonical.source_trace,
        warnings=canonical.warnings,
    )

    with pytest.raises(
        ValueError,
        match="away_ga_per_match",
    ):
        canonical_to_team_stats(broken)


def test_validation_failure_never_reaches_team_stats() -> None:
    result = map_and_validate(
        soccerstats=SoccerStatsData(
            match=make_match(),
            goals=GoalStats(
                home_gf_per_match=-1.0,
                home_ga_per_match=1.0,
                away_gf_per_match=1.0,
                away_ga_per_match=1.0,
            ),
        ),
        required_fields=REQUIRED,
    )

    assert result.valid is False

    with pytest.raises(
        ValueError,
        match="validation başarısız",
    ):
        validated_canonical_to_team_stats(result)


def test_validated_canonical_data_enters_team_stats() -> None:
    result = map_and_validate(
        soccerstats=make_soccerstats(),
        required_fields=REQUIRED,
    )

    assert result.valid is True

    stats = validated_canonical_to_team_stats(
        result
    )

    assert stats.home_gf == 1.50
    assert stats.home_ga == 1.00
    assert stats.away_gf == 1.20
    assert stats.away_ga == 1.10


def test_wrong_canonical_type_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="CanonicalMatchData",
    ):
        canonical_to_team_stats({})  # type: ignore[arg-type]
