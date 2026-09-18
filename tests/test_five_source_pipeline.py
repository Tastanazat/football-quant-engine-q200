from __future__ import annotations

import pytest

from q200_engine.five_source_pipeline import (
    FIVE_SOURCE_PIPELINE_VERSION,
    build_locked_model_from_five_sources,
    run_five_source_analysis,
)
from q200_engine.ingestion.models import (
    FiveSourceMatchInput,
    GoalStats,
    MatchInfo,
    OddsData,
    PPIData,
    SoccerStatsData,
    StatsHubData,
)


def make_input(
    *,
    with_odds: bool = True,
) -> FiveSourceMatchInput:

    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        competition="Spain - LaLiga",
    )

    soccerstats = SoccerStatsData(
        match=match,
        goals=GoalStats(
            home_gf_per_match=1.70,
            home_ga_per_match=0.95,
            away_gf_per_match=0.76,
            away_ga_per_match=1.14,
        ),
    )

    statshub_home = StatsHubData(
        match=match,
        values={
            "goals_for": 1.70,
            "goals_agt": 0.95,
            "xg": 1.50,
            "xga": 1.20,
        },
    )

    statshub_away = StatsHubData(
        match=match,
        values={
            "goals_for": 0.76,
            "goals_agt": 1.14,
            "xg": 0.76,
            "xga": 1.31,
        },
    )

    ppi = PPIData(
        match=match,
        home_ppg=2.40,
        away_ppg=1.00,
        home_ppi=2.33,
        away_ppi=1.25,
    )

    odds = None

    if with_odds:

        odds = OddsData(
            match=match,
            markets={
                "1X2": {
                    "HOME": 1.72,
                    "DRAW": 3.75,
                    "AWAY": 5.80,
                }
            },
        )

    return FiveSourceMatchInput(
        match=match,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        soccerstats=soccerstats,
        ppi=ppi,
        odds=odds,
    )


def test_five_source_pipeline_version():

    assert FIVE_SOURCE_PIPELINE_VERSION == (
        "Q200-FIVE-SOURCE-PIPELINE-V1"
    )


def test_build_locked_model_uses_statistics_before_odds():

    data = make_input()

    pipeline = (
        build_locked_model_from_five_sources(
            data
        )
    )

    assert pipeline.model_locked is True

    assert pipeline.lambda_home > 0

    assert pipeline.lambda_away > 0


def test_odds_do_not_change_locked_model():

    without_odds = make_input(
        with_odds=False
    )

    with_odds = make_input(
        with_odds=True
    )

    model_without_odds = (
        build_locked_model_from_five_sources(
            without_odds
        )
    )

    model_with_odds = (
        build_locked_model_from_five_sources(
            with_odds
        )
    )

    assert (
        model_without_odds.lambda_home
        == model_with_odds.lambda_home
    )

    assert (
        model_without_odds.lambda_away
        == model_with_odds.lambda_away
    )

    assert (
        model_without_odds.probabilities
        == model_with_odds.probabilities
    )


def test_full_five_source_analysis_requires_odds():

    with pytest.raises(
        ValueError,
        match="OddsData",
    ):

        run_five_source_analysis(
            make_input(
                with_odds=False
            ),
            bankroll=50_000,
        )


def test_full_five_source_analysis_returns_locked_result():

    result = run_five_source_analysis(
        make_input(),
        market="1X2",
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    assert result.snapshot.lambda_home > 0

    assert result.snapshot.lambda_away > 0

    assert result.fair_odds

    assert result.ev
