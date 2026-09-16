"""
Q200 Engine - Test Suite

Q200 V3.1

Test kapsamı:

- Schema
- Lambda
- Poisson
- Monte Carlo
- Model Lock
- Stress Test
- Odds / No-Vig
- Fair Odds
- EV
- Selection
- Kelly
- Portfolio Risk Cap
- Backtest
- Pipeline
- Odds -> Model bağımsızlığı
"""

from __future__ import annotations

import math

import pytest

from q200_engine.backtest import (
    BacktestEngine,
    calculate_profit,
    run_backtest,
    settle_bet,
    settle_market,
)
from q200_engine.kelly import quarter_kelly
from q200_engine.markets import (
    all_market_probabilities,
    fair_odds_from_probabilities,
)
from q200_engine.model import build_model, calculate_lambdas
from q200_engine.odds import (
    expected_value,
    implied_probabilities,
    remove_vig,
)
from q200_engine.pipeline import (
    Q200Pipeline,
    run_pipeline,
)
from q200_engine.schema import TeamStats
from q200_engine.selection import (
    MAX_BANKROLL_RISK,
    MINIMUM_ODDS,
    select,
)
from q200_engine.stress_test import (
    stress_lambdas,
    stress_market_probabilities,
)


# =========================================================
# FIXTURES
# =========================================================

@pytest.fixture
def stats() -> TeamStats:
    return TeamStats(
        home_gf=1.8,
        home_ga=1.1,
        away_gf=1.4,
        away_ga=1.3,
        home_xg=1.75,
        home_xga=1.05,
        away_xg=1.35,
        away_xga=1.25,
    )


@pytest.fixture
def bankroll() -> float:
    return 50_000.0


# =========================================================
# MODEL / LAMBDA
# =========================================================

def test_lambda_calculation(stats):
    lambda_home, lambda_away = calculate_lambdas(stats)

    assert lambda_home > 0
    assert lambda_away > 0

    assert math.isclose(
        lambda_home,
        (
            0.35 * stats.home_gf
            + 0.35 * stats.away_ga
            + 0.15 * stats.home_xg
            + 0.15 * stats.away_xga
        ),
        rel_tol=1e-9,
    )

    assert math.isclose(
        lambda_away,
        (
            0.35 * stats.away_gf
            + 0.35 * stats.home_ga
            + 0.15 * stats.away_xg
            + 0.15 * stats.home_xga
        ),
        rel_tol=1e-9,
    )


def test_model_build(stats):
    snapshot = build_model(stats)

    assert snapshot.lambda_home > 0
    assert snapshot.lambda_away > 0

    assert snapshot.locked is True
    assert snapshot.model_locked is True

    assert snapshot.model_version == "Q200-V3.1"

    assert snapshot.probabilities

    assert "HOME" in snapshot.probabilities
    assert "DRAW" in snapshot.probabilities
    assert "AWAY" in snapshot.probabilities

    total_probability = sum(
        snapshot.probabilities.values()
    )

    assert math.isclose(
        total_probability,
        1.0,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


# =========================================================
# POISSON / MARKET
# =========================================================

def test_all_market_probabilities(stats):
    lambda_home, lambda_away = calculate_lambdas(
        stats
    )

    markets = all_market_probabilities(
        lambda_home,
        lambda_away,
    )

    assert markets

    assert "HOME" in markets
    assert "DRAW" in markets
    assert "AWAY" in markets

    assert "OVER_2.5" in markets
    assert "UNDER_2.5" in markets

    assert "BTTS_YES" in markets
    assert "BTTS_NO" in markets


def test_market_probabilities_are_valid(stats):
    lambda_home, lambda_away = calculate_lambdas(
        stats
    )

    markets = all_market_probabilities(
        lambda_home,
        lambda_away,
    )

    for outcome, probability in markets.items():

        assert 0 <= probability <= 1, outcome

        assert math.isfinite(
            probability
        ), outcome


# =========================================================
# MONTE CARLO
# =========================================================

def test_monte_carlo_exists(stats):
    snapshot = build_model(stats)

    assert snapshot.monte_carlo_probabilities

    for probability in (
        snapshot.monte_carlo_probabilities.values()
    ):
        assert 0 <= probability <= 1


# =========================================================
# MODEL LOCK
# =========================================================

def test_model_is_locked(stats):
    pipeline = Q200Pipeline(stats)

    assert pipeline.model_locked is True

    before_home = pipeline.lambda_home
    before_away = pipeline.lambda_away
    before_probabilities = pipeline.probabilities.copy()

    assert before_home > 0
    assert before_away > 0
    assert before_probabilities

    assert pipeline.snapshot.locked is True


# =========================================================
# STRESS TEST
# =========================================================

def test_stress_lambdas(stats):
    lambda_home, lambda_away = calculate_lambdas(
        stats
    )

    stressed = stress_lambdas(
        lambda_home,
        lambda_away,
    )

    assert "OPTIMISTIC" in stressed
    assert "BASELINE" in stressed
    assert "PESSIMISTIC" in stressed

    assert (
        stressed["OPTIMISTIC"]["lambda_home"]
        > stressed["BASELINE"]["lambda_home"]
    )

    assert (
        stressed["OPTIMISTIC"]["lambda_away"]
        < stressed["BASELINE"]["lambda_away"]
    )

    assert (
        stressed["PESSIMISTIC"]["lambda_home"]
        < stressed["BASELINE"]["lambda_home"]
    )

    assert (
        stressed["PESSIMISTIC"]["lambda_away"]
        > stressed["BASELINE"]["lambda_away"]
    )


def test_stress_market_probabilities(stats):
    lambda_home, lambda_away = calculate_lambdas(
        stats
    )

    stressed = stress_market_probabilities(
        lambda_home,
        lambda_away,
    )

    assert "OPTIMISTIC" in stressed
    assert "BASELINE" in stressed
    assert "PESSIMISTIC" in stressed

    for scenario in stressed.values():

        assert scenario

        for probability in scenario.values():
            assert 0 <= probability <= 1


# =========================================================
# ODDS / NO-VIG
# =========================================================

def test_implied_probabilities():
    odds = {
        "HOME": 2.00,
        "DRAW": 3.50,
        "AWAY": 4.00,
    }

    implied = implied_probabilities(odds)

    assert set(implied) == set(odds)

    for probability in implied.values():
        assert probability > 0
        assert probability < 1


def test_remove_vig():
    odds = {
        "HOME": 2.00,
        "DRAW": 3.50,
        "AWAY": 4.00,
    }

    no_vig = remove_vig(
        implied_probabilities(odds)
    )

    total = sum(no_vig.values())

    assert math.isclose(
        total,
        1.0,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


# =========================================================
# FAIR ODDS
# =========================================================

def test_fair_odds():
    probabilities = {
        "HOME": 0.50,
        "DRAW": 0.25,
        "AWAY": 0.25,
    }

    fair = fair_odds_from_probabilities(
        probabilities
    )

    assert math.isclose(
        fair["HOME"],
        2.0,
    )

    assert math.isclose(
        fair["DRAW"],
        4.0,
    )

    assert math.isclose(
        fair["AWAY"],
        4.0,
    )


# =========================================================
# EV
# =========================================================

def test_expected_value():
    ev = expected_value(
        probability=0.60,
        odds=2.00,
    )

    assert math.isclose(
        ev,
        0.20,
    )


def test_positive_ev():
    ev = expected_value(
        probability=0.60,
        odds=2.00,
    )

    assert ev > 0


def test_negative_ev():
    ev = expected_value(
        probability=0.40,
        odds=2.00,
    )

    assert ev < 0


# =========================================================
# KELLY
# =========================================================

def test_quarter_kelly():
    result = quarter_kelly(
        probability=0.60,
        odds=2.00,
        bankroll=50_000,
    )

    assert result["full_kelly"] > 0
    assert result["quarter_kelly"] > 0
    assert result["stake"] > 0

    assert (
        result["stake"]
        <= 50_000 * MAX_BANKROLL_RISK
    )


def test_kelly_bankroll_cap():
    result = quarter_kelly(
        probability=0.99,
        odds=5.00,
        bankroll=50_000,
    )

    assert (
        result["stake"]
        <= 50_000 * MAX_BANKROLL_RISK
    )


# =========================================================
# SELECTION
# =========================================================

def test_selection_eligible():
    probabilities = {
        "HOME": 0.60,
        "DRAW": 0.20,
        "AWAY": 0.20,
    }

    odds = {
        "HOME": 2.00,
        "DRAW": 3.50,
        "AWAY": 4.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result

    home = next(
        row
        for row in result
        if row["outcome"] == "HOME"
    )

    assert home["eligible"] is True
    assert home["ev"] >= 0.08
    assert home["stake"] > 0


def test_selection_minimum_odds_filter():
    probabilities = {
        "HOME": 0.80,
        "DRAW": 0.10,
        "AWAY": 0.10,
    }

    odds = {
        "HOME": 1.40,
        "DRAW": 1.30,
        "AWAY": 1.20,
    }

    with pytest.raises(ValueError):
        select(
            probabilities,
            odds,
            bankroll=50_000,
            uncertainty="LOW",
        )


def test_selection_skips_missing_odds():
    probabilities = {
        "HOME": 0.60,
        "DRAW": 0.20,
        "AWAY": 0.20,
    }

    odds = {
        "HOME": 2.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=50_000,
        uncertainty="LOW",
    )

    assert len(result) == 1
    assert result[0]["outcome"] == "HOME"


def test_selection_very_high_uncertainty():
    probabilities = {
        "HOME": 0.50,
        "DRAW": 0.25,
        "AWAY": 0.25,
    }

    odds = {
        "HOME": 2.00,
        "DRAW": 3.50,
        "AWAY": 4.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=50_000,
        uncertainty="VERY_HIGH",
    )

    assert len(result) == 3

    for row in result:
        assert row["eligible"] is False
        assert row["stake"] == 0.0
        assert row["quarter_kelly"] == 0.0
        assert row["reason"] == (
            "VERY_HIGH uncertainty -> NO BET"
        )


# =========================================================
# NEW: PORTFOLIO RISK CAP
# =========================================================

def test_total_selected_stakes_respect_two_percent_cap():
    """
    Birden fazla eligible seçim olsa bile
    toplam stake bankroll'un %2'sini geçemez.
    """

    bankroll = 50_000.0

    probabilities = {
        "HOME": 0.80,
        "DRAW": 0.70,
        "AWAY": 0.60,
    }

    odds = {
        "HOME": 2.00,
        "DRAW": 2.00,
        "AWAY": 2.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=bankroll,
        uncertainty="LOW",
    )

    total_stake = sum(
        row["stake"]
        for row in result
        if row["eligible"]
    )

    maximum_allowed = (
        bankroll * MAX_BANKROLL_RISK
    )

    assert total_stake <= (
        maximum_allowed + 1e-9
    )


def test_portfolio_risk_cap_is_exactly_two_percent_when_needed():
    """
    Kelly stake toplamı %2'yi aşarsa
    sistem toplamı %2'ye ölçeklemelidir.
    """

    bankroll = 50_000.0

    probabilities = {
        "A": 0.95,
        "B": 0.90,
        "C": 0.85,
    }

    odds = {
        "A": 2.00,
        "B": 2.00,
        "C": 2.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=bankroll,
        uncertainty="LOW",
    )

    eligible = [
        row
        for row in result
        if row["eligible"]
    ]

    assert len(eligible) == 3

    total_stake = sum(
        row["stake"]
        for row in eligible
    )

    maximum_allowed = (
        bankroll * MAX_BANKROLL_RISK
    )

    assert math.isclose(
        total_stake,
        maximum_allowed,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


def test_single_selection_stays_unchanged_under_cap():
    """
    Tek seçim zaten %2'nin altındaysa
    portfolio cap gereksiz yere stake'i azaltmamalıdır.
    """

    bankroll = 50_000.0

    probabilities = {
        "HOME": 0.55,
    }

    odds = {
        "HOME": 2.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=bankroll,
        uncertainty="LOW",
    )

    row = result[0]

    assert row["eligible"] is True
    assert row["stake"] > 0

    assert row["stake"] <= (
        bankroll * MAX_BANKROLL_RISK
    )


def test_no_bet_has_zero_portfolio_risk():
    probabilities = {
        "HOME": 0.40,
        "DRAW": 0.30,
        "AWAY": 0.30,
    }

    odds = {
        "HOME": 1.50,
        "DRAW": 1.50,
        "AWAY": 1.50,
    }

    result = select(
        probabilities,
        odds,
        bankroll=50_000,
        uncertainty="HIGH",
    )

    total_stake = sum(
        row["stake"]
        for row in result
    )

    assert total_stake == 0.0


# =========================================================
# BACKTEST
# =========================================================

def test_settle_market():
    assert settle_market(
        "HOME",
        2,
        1,
    ) == "WIN"

    assert settle_market(
        "DRAW",
        1,
        1,
    ) == "WIN"

    assert settle_market(
        "AWAY",
        1,
        2,
    ) == "WIN"

    assert settle_market(
        "HOME",
        1,
        2,
    ) == "LOSS"

    assert settle_market(
        "OVER_2.5",
        2,
        1,
    ) == "WIN"

    assert settle_market(
        "UNDER_2.5",
        1,
        1,
    ) == "WIN"

    assert settle_market(
        "BTTS_YES",
        2,
        1,
    ) == "WIN"

    assert settle_market(
        "BTTS_NO",
        2,
        1,
    ) == "LOSS"

    assert settle_market(
        "2-1",
        2,
        1,
    ) == "WIN"


def test_calculate_profit():
    assert math.isclose(
        calculate_profit(
            "WIN",
            100,
            2.00,
        ),
        100.0,
    )

    assert math.isclose(
        calculate_profit(
            "LOSS",
            100,
            2.00,
        ),
        -100.0,
    )

    assert math.isclose(
        calculate_profit(
            "VOID",
            100,
            2.00,
        ),
        0.0,
    )


def test_settle_bet():
    result = settle_bet(
        outcome="HOME",
        home_goals=2,
        away_goals=1,
        stake=100,
        odds=2.00,
    )

    assert result.settlement == "WIN"
    assert math.isclose(
        result.profit,
        100.0,
    )


def test_backtest_engine():
    engine = BacktestEngine()

    engine.add_bet(
        outcome="HOME",
        home_goals=2,
        away_goals=1,
        stake=100,
        odds=2.00,
    )

    engine.add_bet(
        outcome="AWAY",
        home_goals=2,
        away_goals=1,
        stake=100,
        odds=2.00,
    )

    summary = engine.summary()

    assert summary.total_bets == 2
    assert summary.wins == 1
    assert summary.losses == 1
    assert math.isclose(
        summary.profit,
        0.0,
    )


def test_run_backtest():
    bets = [
        {
            "outcome": "HOME",
            "home_goals": 2,
            "away_goals": 1,
            "stake": 100,
            "odds": 2.00,
        },
        {
            "outcome": "AWAY",
            "home_goals": 2,
            "away_goals": 1,
            "stake": 100,
            "odds": 2.00,
        },
    ]

    summary = run_backtest(bets)

    assert summary.total_bets == 2
    assert summary.wins == 1
    assert summary.losses == 1


# =========================================================
# PIPELINE
# =========================================================

def test_pipeline_stress_test(stats):
    pipeline = Q200Pipeline(stats)

    result = pipeline.stress_test()

    assert "lambdas" in result
    assert "probabilities" in result

    assert "OPTIMISTIC" in result["lambdas"]
    assert "BASELINE" in result["lambdas"]
    assert "PESSIMISTIC" in result["lambdas"]


def test_pipeline_analysis(stats):
    pipeline = Q200Pipeline(stats)

    odds = {
        "HOME": 2.20,
        "DRAW": 3.40,
        "AWAY": 3.20,
    }

    result = pipeline.analyze_odds(
        odds=odds,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True

    assert result.fair_odds
    assert result.no_vig_probabilities
    assert result.ev

    assert result.stress_lambdas
    assert result.stress_probabilities

    assert result.pessimistic_probabilities
    assert result.pessimistic_ev

    assert result.selections


def test_pipeline_very_high_uncertainty_produces_no_bet(
    stats,
):
    pipeline = Q200Pipeline(stats)

    odds = {
        "HOME": 2.20,
        "DRAW": 3.40,
        "AWAY": 3.20,
    }

    result = pipeline.analyze_odds(
        odds=odds,
        bankroll=50_000,
        uncertainty="VERY_HIGH",
    )

    assert len(result.selections) == 3

    for selection in result.selections:
        assert selection["eligible"] is False
        assert selection["stake"] == 0.0


def test_pipeline_model_lock_after_complete_flow(stats):
    pipeline = Q200Pipeline(stats)

    original_home = pipeline.lambda_home
    original_away = pipeline.lambda_away
    original_probabilities = (
        pipeline.probabilities.copy()
    )

    odds = {
        "HOME": 2.20,
        "DRAW": 3.40,
        "AWAY": 3.20,
    }

    pipeline.analyze_odds(
        odds=odds,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert pipeline.model_locked is True

    assert math.isclose(
        pipeline.lambda_home,
        original_home,
    )

    assert math.isclose(
        pipeline.lambda_away,
        original_away,
    )

    assert (
        pipeline.probabilities
        == original_probabilities
    )


def test_odds_cannot_change_model(
    stats,
):
    pipeline = Q200Pipeline(stats)

    original_home = pipeline.lambda_home
    original_away = pipeline.lambda_away

    odds_1 = {
        "HOME": 1.50,
        "DRAW": 5.00,
        "AWAY": 8.00,
    }

    odds_2 = {
        "HOME": 4.00,
        "DRAW": 2.00,
        "AWAY": 1.80,
    }

    pipeline.analyze_odds(
        odds=odds_1,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    pipeline.analyze_odds(
        odds=odds_2,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert math.isclose(
        pipeline.lambda_home,
        original_home,
    )

    assert math.isclose(
        pipeline.lambda_away,
        original_away,
    )


def test_odds_cannot_change_pessimistic_probabilities(
    stats,
):
    pipeline = Q200Pipeline(stats)

    odds_1 = {
        "HOME": 1.80,
        "DRAW": 3.50,
        "AWAY": 4.50,
    }

    odds_2 = {
        "HOME": 4.00,
        "DRAW": 2.10,
        "AWAY": 1.90,
    }

    result_1 = pipeline.analyze_odds(
        odds=odds_1,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    result_2 = pipeline.analyze_odds(
        odds=odds_2,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert (
        result_1.pessimistic_probabilities
        == result_2.pessimistic_probabilities
    )


def test_pipeline_portfolio_risk_cap(stats):
    """
    Pipeline üzerinden gelen seçimlerde de
    toplam bankroll riski %2'yi geçmemelidir.
    """

    pipeline = Q200Pipeline(stats)

    odds = {
        "HOME": 2.00,
        "DRAW": 2.00,
        "AWAY": 2.00,
    }

    bankroll = 50_000.0

    result = pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty="LOW",
    )

    total_stake = sum(
        row["stake"]
        for row in result.selections
        if row["eligible"]
    )

    assert total_stake <= (
        bankroll * MAX_BANKROLL_RISK
        + 1e-9
    )


# =========================================================
# CONVENIENCE FLOW
# =========================================================

def test_run_pipeline(stats):
    odds = {
        "HOME": 2.20,
        "DRAW": 3.40,
        "AWAY": 3.20,
    }

    result = run_pipeline(
        stats=stats,
        odds=odds,
        bankroll=50_000,
        uncertainty="MEDIUM",
    )

    assert result.snapshot.locked is True
    assert result.selections


# =========================================================
# VALIDATION TESTS
# =========================================================

def test_invalid_odds():
    probabilities = {
        "HOME": 0.60,
    }

    odds = {
        "HOME": 1.0,
    }

    with pytest.raises(ValueError):
        select(
            probabilities,
            odds,
            bankroll=50_000,
        )


def test_invalid_bankroll():
    probabilities = {
        "HOME": 0.60,
    }

    odds = {
        "HOME": 2.00,
    }

    with pytest.raises(ValueError):
        select(
            probabilities,
            odds,
            bankroll=0,
        )


def test_empty_odds():
    probabilities = {
        "HOME": 0.60,
    }

    with pytest.raises(ValueError):
        select(
            probabilities,
            {},
            bankroll=50_000,
        )


def test_non_dict_odds():
    probabilities = {
        "HOME": 0.60,
    }

    with pytest.raises(TypeError):
        select(
            probabilities,
            [],
            bankroll=50_000,
        )


def test_invalid_uncertainty():
    probabilities = {
        "HOME": 0.60,
    }

    odds = {
        "HOME": 2.00,
    }

    with pytest.raises(ValueError):
        select(
            probabilities,
            odds,
            bankroll=50_000,
            uncertainty="EXTREME",
        )


def test_invalid_probability():
    probabilities = {
        "HOME": 1.50,
    }

    odds = {
        "HOME": 2.00,
    }

    with pytest.raises(ValueError):
        select(
            probabilities,
            odds,
            bankroll=50_000,
        )


# =========================================================
# FINAL INTEGRITY
# =========================================================

def test_selection_never_exceeds_individual_risk_cap():
    bankroll = 50_000.0

    probabilities = {
        "A": 0.90,
        "B": 0.80,
        "C": 0.70,
    }

    odds = {
        "A": 2.00,
        "B": 2.00,
        "C": 2.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=bankroll,
        uncertainty="LOW",
    )

    individual_cap = (
        bankroll * MAX_BANKROLL_RISK
    )

    for row in result:
        assert row["stake"] <= (
            individual_cap + 1e-9
        )


def test_selection_total_risk_is_never_above_two_percent():
    bankroll = 50_000.0

    probabilities = {
        "A": 0.99,
        "B": 0.98,
        "C": 0.97,
        "D": 0.96,
        "E": 0.95,
    }

    odds = {
        "A": 2.00,
        "B": 2.00,
        "C": 2.00,
        "D": 2.00,
        "E": 2.00,
    }

    result = select(
        probabilities,
        odds,
        bankroll=bankroll,
        uncertainty="LOW",
    )

    total_stake = sum(
        row["stake"]
        for row in result
    )

    assert total_stake <= (
        bankroll * 0.02 + 1e-9
    )
