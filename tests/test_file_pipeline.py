import pytest


def test_run_pipeline_from_canonical_sources():
    from q200_engine.ingestion.models import (
        GoalStats,
        MatchInfo,
        SoccerStatsData,
        StatsHubData,
    )
    from q200_engine.file_pipeline import (
        run_pipeline_from_sources,
    )

    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="17 Sep 2026",
        time="18:00",
        competition="LaLiga",
        source="SoccerSTATS",
    )

    soccerstats = SoccerStatsData(
        match=match,
        goals=GoalStats(
            home_gf_per_match=1.50,
            home_ga_per_match=1.00,
            away_gf_per_match=1.20,
            away_ga_per_match=1.10,
        ),
    )

    statshub = StatsHubData(
        match=match,
        values={
            "possession_avg": 50.85,
            "total_shots_avg": 26.50,
            "shots_on_target_avg": 10.50,
            "corners_avg": 9.15,
        },
    )

    result = run_pipeline_from_sources(
        soccerstats=soccerstats,
        statshub=statshub,
        odds={
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        bankroll=50_000,
    )

    assert result.snapshot.locked is True
    assert result.snapshot.model_version == "Q200-V3.1"
    assert result.snapshot.lambda_home > 0
    assert result.snapshot.lambda_away > 0


def test_canonical_source_pipeline_preserves_source_priority():
    from q200_engine.ingestion.models import (
        GoalStats,
        MatchInfo,
        SoccerStatsData,
        StatsHubData,
    )
    from q200_engine.ingestion.validated_pipeline import (
        map_and_validate,
    )

    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        source="SoccerSTATS",
    )

    result = map_and_validate(
        soccerstats=SoccerStatsData(
            match=match,
            goals=GoalStats(
                home_gf_per_match=1.50,
                home_ga_per_match=1.00,
                away_gf_per_match=1.20,
                away_ga_per_match=1.10,
            ),
        ),
        statshub=StatsHubData(
            match=match,
            values={
                "home_gf_per_match": 99.0,
                "possession_avg": 50.85,
            },
        ),
    )

    assert result.valid is True
    assert (
        result.canonical_values["home_gf_per_match"]
        == 1.50
    )
    assert (
        result.source_trace["home_gf_per_match"]
        == "SoccerSTATS"
    )
    assert (
        result.canonical_values["possession_avg"]
        == 50.85
    )


def test_canonical_source_pipeline_blocks_invalid_validation():
    from q200_engine.file_pipeline import (
        run_pipeline_from_sources,
    )
    from q200_engine.ingestion.models import (
        GoalStats,
        MatchInfo,
        SoccerStatsData,
    )

    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        source="SoccerSTATS",
    )

    soccerstats = SoccerStatsData(
        match=match,
        goals=GoalStats(
            home_gf_per_match=-1.0,
            home_ga_per_match=1.0,
            away_gf_per_match=1.20,
            away_ga_per_match=1.10,
        ),
    )

    with pytest.raises(
        ValueError,
        match="validation başarısız",
    ):
        run_pipeline_from_sources(
            soccerstats=soccerstats,
            odds={"HOME": 2.00},
            bankroll=50_000,
        )
