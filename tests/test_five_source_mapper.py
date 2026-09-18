from __future__ import annotations

from q200_engine.ingestion.models import (
    CornerStats,
    FormStats,
    GoalStats,
    MatchInfo,
    SoccerStatsData,
    StatsHubData,
)

from q200_engine.ingestion.source_mapper import (
    SOURCE_MAPPER_VERSION,
    map_soccerstats,
    map_sources,
)


def make_soccerstats():
    return SoccerStatsData(
        match=MatchInfo(
            home_team="Real Betis",
            away_team="Getafe",
            source="SoccerSTATS",
        ),
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
        corners=CornerStats(
            home_corners_for=5.0,
            home_corners_against=7.5,
            away_corners_for=3.0,
            away_corners_against=3.0,
            home_total_corners=12.5,
            away_total_corners=6.0,
        ),
        form=FormStats(
            home_ppg=3.0,
            away_ppg=0.0,
        ),
    )


def test_source_mapper_version():
    assert (
        SOURCE_MAPPER_VERSION
        == "Q200-SOURCE-MAPPER-V2"
    )


def test_map_soccerstats_creates_canonical_fields():
    data = make_soccerstats()

    values, trace = map_soccerstats(
        data
    )

    assert (
        values["home_gf"]
        == 2.0
    )

    assert (
        values["home_ga"]
        == 0.0
    )

    assert (
        values["away_gf"]
        == 0.0
    )

    assert (
        values["away_ga"]
        == 4.0
    )

    assert (
        values["home_gf_per_match"]
        == 1.0
    )

    assert (
        values["away_ga_per_match"]
        == 2.0
    )

    assert (
        values["home_corners_for"]
        == 5.0
    )

    assert (
        values["home_corners_against"]
        == 7.5
    )

    assert (
        values["away_corners_for"]
        == 3.0
    )

    assert (
        values["away_corners_against"]
        == 3.0
    )

    assert (
        values["home_ppg"]
        == 3.0
    )

    assert (
        values["away_ppg"]
        == 0.0
    )

    assert (
        trace["home_gf_per_match"]
        == "SoccerSTATS"
    )

    assert (
        trace["home_corners_for"]
        == "SoccerSTATS"
    )


def test_none_values_are_not_inserted():
    data = SoccerStatsData(
        match=MatchInfo(
            home_team="A",
            away_team="B",
        ),
        goals=GoalStats(
            home_gf_per_match=1.2,
        ),
    )

    values, trace = map_soccerstats(
        data
    )

    assert (
        values["home_gf_per_match"]
        == 1.2
    )

    assert (
        "away_gf_per_match"
        not in values
    )

    assert (
        "away_gf_per_match"
        not in trace
    )


def test_stats_hub_fills_missing_soccerstats_fields():
    soccerstats = SoccerStatsData(
        match=MatchInfo(
            home_team="A",
            away_team="B",
        ),
        goals=GoalStats(
            home_gf_per_match=1.2,
        ),
    )

    statshub = StatsHubData(
        match=MatchInfo(
            home_team="A",
            away_team="B",
        ),
        values={
            "shots": 25.0,
            "possession": 55.0,
        },
    )

    result = map_sources(
        soccerstats=soccerstats,
        statshub=statshub,
    )

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.2
    )

    assert (
        result.canonical_values[
            "shots"
        ]
        == 25.0
    )

    assert (
        result.canonical_values[
            "possession"
        ]
        == 55.0
    )

    assert (
        result.source_trace[
            "shots"
        ]
        == "StatsHub"
    )

    assert (
        result.source_trace[
            "possession"
        ]
        == "StatsHub"
    )


def test_soccerstats_has_priority_over_statshub():
    soccerstats = SoccerStatsData(
        match=MatchInfo(
            home_team="A",
            away_team="B",
        ),
        goals=GoalStats(
            home_gf_per_match=1.5,
        ),
    )

    statshub = StatsHubData(
        match=MatchInfo(
            home_team="A",
            away_team="B",
        ),
        values={
            "home_gf_per_match": 9.9,
        },
    )

    result = map_sources(
        soccerstats=soccerstats,
        statshub=statshub,
    )

    assert (
        result.canonical_values[
            "home_gf_per_match"
        ]
        == 1.5
    )

    assert any(
        "home_gf_per_match"
        in warning
        for warning in result.warnings
    )

    assert (
        result.source_trace[
            "home_gf_per_match"
        ]
        == "SoccerSTATS"
    )


def test_stats_hub_can_be_used_alone():
    statshub = StatsHubData(
        match=MatchInfo(
            home_team="A",
            away_team="B",
        ),
        values={
            "shots": 30.0,
            "possession": 60.0,
        },
    )

    result = map_sources(
        statshub=statshub,
    )

    assert (
        result.match.home_team
        == "A"
    )

    assert (
        result.match.away_team
        == "B"
    )

    assert (
        result.canonical_values[
            "shots"
        ]
        == 30.0
    )

    assert (
        result.source_trace[
            "shots"
        ]
        == "StatsHub"
    )


def test_map_sources_requires_source():
    try:
        map_sources()
    except ValueError as exc:
        assert (
            "En az bir statistics source"
            in str(exc)
        )
    else:
        raise AssertionError(
            "ValueError bekleniyordu."
        )
