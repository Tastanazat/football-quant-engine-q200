from __future__ import annotations

import pytest

from q200_engine.ingestion.models import (
    GoalStats,
    MatchInfo,
    OddsData,
    PPIData,
    SoccerStatsData,
    StatsHubData,
)

from q200_engine.ingestion.source_mapper import (
    SOURCE_MAPPER_VERSION,
    map_five_sources,
    map_sources,
)


def make_match():
    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        competition="LaLiga",
    )


def make_soccerstats():
    return SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            home_gf_per_match=1.00,
            home_ga_per_match=0.00,
            away_gf_per_match=0.00,
            away_ga_per_match=2.00,
        ),
    )


def make_statshub_home():
    return StatsHubData(
        match=make_match(),
        values={
            "goals_avg": 3.05,
            "goals_for": 1.70,
            "goals_agt": 1.35,
            "xg_avg": 2.92,
            "xg_for": 1.50,
            "xg_agt": 1.41,
            "total_shots_avg": 26.50,
            "total_shots_for": 15.05,
            "shots_on_target_for": 5.65,
        },
    )


def make_statshub_away():
    return StatsHubData(
        match=make_match(),
        values={
            "goals_avg": 1.85,
            "goals_for": 0.95,
            "goals_agt": 0.90,
            "xg_avg": 1.90,
            "xg_for": 0.76,
            "xg_agt": 1.14,
            "total_shots_avg": 21.75,
            "total_shots_for": 9.25,
            "shots_on_target_for": 2.80,
        },
    )


def make_ppi():
    return PPIData(
        match=make_match(),
        home_ppg=2.40,
        away_ppg=1.00,
        home_ppi=2.33,
        away_ppi=1.25,
    )


def make_odds():
    return OddsData(
        match=make_match(),
        markets={
            "1X2": {
                "home": 1.72,
                "draw": 3.75,
                "away": 5.80,
            }
        },
    )


def test_mapper_version():
    assert (
        SOURCE_MAPPER_VERSION
        == "Q200-SOURCE-MAPPER-V2"
    )


def test_five_source_mapper_accepts_all_sources():
    result = map_five_sources(
        soccerstats=make_soccerstats(),
        statshub_home=make_statshub_home(),
        statshub_away=make_statshub_away(),
        ppi=make_ppi(),
        odds=make_odds(),
    )

    assert (
        result.match.home_team
        == "Real Betis"
    )

    assert (
        result.match.away_team
        == "Getafe"
    )

    assert (
        result.statshub_home
        is not None
    )

    assert (
        result.statshub_away
        is not None
    )

    assert (
        result.ppi
        is not None
    )

    assert (
        result.odds
        is not None
    )


def test_soccerstats_has_priority_for_model_fields():
    result = map_five_sources(
        soccerstats=make_soccerstats(),
        statshub_home=make_statshub_home(),
        statshub_away=make_statshub_away(),
    )

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.00
    )

    assert (
        result.canonical_values[
            "home_ga_per_match"
        ]
        == 0.00
    )

    assert (
        result.canonical_values[
            "away_gf_per_match"
        ]
        == 0.00
    )

    assert (
        result.canonical_values[
            "away_ga_per_match"
        ]
        == 2.00
    )


def test_statshub_home_can_fill_missing_home_fields():
    soccerstats = SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            away_gf_per_match=0.50,
            away_ga_per_match=1.50,
        ),
    )

    result = map_five_sources(
        soccerstats=soccerstats,
        statshub_home=make_statshub_home(),
    )

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.70
    )

    assert (
        result.canonical_values[
            "home_ga_per_match"
        ]
        == 1.35
    )

    assert (
        result.source_trace[
            "home_gf_per_match"
        ]
        == "StatsHub HOME"
    )


def test_statshub_away_can_fill_missing_away_fields():
    soccerstats = SoccerStatsData(
        match=make_match(),
        goals=GoalStats(
            home_gf_per_match=1.20,
            home_ga_per_match=0.80,
        ),
    )

    result = map_five_sources(
        soccerstats=soccerstats,
        statshub_away=make_statshub_away(),
    )

    assert (
        result.canonical_values[
            "away_gf_per_match"
        ]
        == 0.95
    )

    assert (
        result.canonical_values[
            "away_ga_per_match"
        ]
        == 0.90
    )

    assert (
        result.source_trace[
            "away_gf_per_match"
        ]
        == "StatsHub AWAY"
    )


def test_statshub_xg_mapping_is_explicit():
    result = map_five_sources(
        statshub_home=make_statshub_home(),
        statshub_away=make_statshub_away(),
    )

    assert (
        result.canonical_values[
            "home_xg"
        ]
        == 1.50
    )

    assert (
        result.canonical_values[
            "home_xga"
        ]
        == 1.41
    )

    assert (
        result.canonical_values[
            "away_xg"
        ]
        == 0.76
    )

    assert (
        result.canonical_values[
            "away_xga"
        ]
        == 1.14
    )


def test_ppi_is_preserved_as_context():
    result = map_five_sources(
        soccerstats=make_soccerstats(),
        ppi=make_ppi(),
    )

    assert (
        result.canonical_values[
            "ppi_home_ppg"
        ]
        == 2.40
    )

    assert (
        result.canonical_values[
            "ppi_away_ppg"
        ]
        == 1.00
    )

    assert (
        result.canonical_values[
            "ppi_home_ppi"
        ]
        == 2.33
    )

    assert (
        result.canonical_values[
            "ppi_away_ppi"
        ]
        == 1.25
    )

    assert (
        result.source_trace[
            "ppi_home_ppi"
        ]
        == "PPI"
    )


def test_odds_are_not_inserted_into_canonical_model_values():
    result = map_five_sources(
        soccerstats=make_soccerstats(),
        odds=make_odds(),
    )

    assert result.odds is not None

    assert (
        "home"
        not in result.canonical_values
    )

    assert (
        "draw"
        not in result.canonical_values
    )

    assert (
        "away"
        not in result.canonical_values
    )


def test_namespaced_statshub_values_are_preserved():
    result = map_five_sources(
        statshub_home=make_statshub_home(),
        statshub_away=make_statshub_away(),
    )

    assert (
        result.canonical_values[
            "statshub_home_goals_avg"
        ]
        == 3.05
    )

    assert (
        result.canonical_values[
            "statshub_away_goals_avg"
        ]
        == 1.85
    )

    assert (
        result.source_trace[
            "statshub_home_goals_avg"
        ]
        == "StatsHub HOME"
    )

    assert (
        result.source_trace[
            "statshub_away_goals_avg"
        ]
        == "StatsHub AWAY"
    )


def test_wrong_match_is_rejected():
    wrong_match = MatchInfo(
        home_team="Barcelona",
        away_team="Getafe",
    )

    wrong_source = StatsHubData(
        match=wrong_match,
        values={
            "goals_for": 1.5,
            "goals_agt": 1.0,
        },
    )

    with pytest.raises(ValueError):
        map_five_sources(
            soccerstats=make_soccerstats(),
            statshub_home=wrong_source,
        )


def test_legacy_map_sources_still_works():
    result = map_sources(
        soccerstats=make_soccerstats(),
    )

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.00
    )

    assert (
        result.canonical_values[
            "away_ga_per_match"
        ]
        == 2.00
    )


def test_no_source_is_rejected():
    with pytest.raises(ValueError):
        map_five_sources()
