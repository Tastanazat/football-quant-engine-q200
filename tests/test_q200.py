import pytest

from q200_engine.schema import TeamStats
from q200_engine.model import calculate_lambdas, build_model
from q200_engine.poisson_model import poisson_match_probabilities
from q200_engine.monte_carlo import simulate_match
from q200_engine.odds import implied_probabilities
from q200_engine.selection import select
from q200_engine.kelly import quarter_kelly
from q200_engine.pipeline import Q200Pipeline

from q200_engine.backtest import (
    settle_market,
    calculate_profit,
    settle_bet,
    BacktestEngine,
    run_backtest,
)


# =========================================================
# LAMBDA
# =========================================================

def test_lambda_formula():

    s = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    h, a = calculate_lambdas(s)

    assert h == pytest.approx(1.705)
    assert a == pytest.approx(1.305)


# =========================================================
# POISSON
# =========================================================

def test_probabilities_sum_to_one():

    p = poisson_match_probabilities(
        1.5,
        1.1,
    )

    assert sum(
        p.values()
    ) == pytest.approx(
        1.0,
        abs=1e-12,
    )


# =========================================================
# MODEL LOCK
# =========================================================

def test_model_is_locked():

    s = TeamStats(
        2,
        1,
        1,
    )

    snap = build_model(s)

    assert snap.locked is True
    assert snap.model_locked is True


# =========================================================
# MONTE CARLO
# =========================================================

def test_monte_carlo_minimum():

    with pytest.raises(ValueError):

        simulate_match(
            1.2,
            1.0,
            iterations=999,
        )


# =========================================================
# NO VIG
# =========================================================

def test_no_vig_sums_to_one():

    p = implied_probabilities({
        "HOME": 2.0,
        "DRAW": 3.5,
        "AWAY": 4.0,
    })

    assert sum(
        p.values()
    ) == pytest.approx(1.0)


# =========================================================
# KELLY
# =========================================================

def test_quarter_kelly_respects_two_percent_cap():

    result = quarter_kelly(
        0.70,
        2.0,
        50_000,
    )

    assert result["stake"] <= 1000


# =========================================================
# MINIMUM ODDS
# =========================================================

def test_minimum_odds_filter():

    with pytest.raises(ValueError):

        select(
            {
                "HOME": 0.60,
                "DRAW": 0.20,
                "AWAY": 0.20,
            },
            {
                "HOME": 1.40,
                "DRAW": 1.45,
                "AWAY": 1.49,
            },
            50_000,
        )


# =========================================================
# EV SELECTION
# =========================================================

def test_ev_can_create_eligible_selection():

    rows = select(
        {
            "HOME": 0.60,
            "DRAW": 0.20,
            "AWAY": 0.20,
        },
        {
            "HOME": 2.0,
            "DRAW": 4.0,
            "AWAY": 5.0,
        },
        50_000,
        uncertainty="LOW",
    )

    assert rows[0]["outcome"] == "HOME"
    assert rows[0]["eligible"] is True


# =========================================================
# MODEL INDEPENDENCE
# =========================================================

def test_pipeline_keeps_model_independent_of_odds():

    s = TeamStats(
        2,
        1,
        1.2,
        1.4,
        1.7,
        1.0,
        1.1,
        1.3,
    )

    p = Q200Pipeline(s)

    before = p.snapshot

    p.analyze_odds(
        {
            "HOME": 2.0,
            "DRAW": 3.5,
            "AWAY": 4.0,
        },
        50_000,
    )

    assert p.snapshot == before
    assert p.snapshot.locked is True


# =========================================================
# Q200 V3.1 - ADDITIONAL SAFETY TESTS
# =========================================================


# =========================================================
# VERY HIGH UNCERTAINTY
# =========================================================

def test_very_high_uncertainty_is_no_bet():

    rows = select(
        {
            "HOME": 0.60,
            "DRAW": 0.20,
            "AWAY": 0.20,
        },
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
        uncertainty="VERY_HIGH",
    )

    assert len(rows) == 3

    for row in rows:

        assert row["eligible"] is False
        assert row["stake"] == 0.0
        assert "NO BET" in row["reason"]


# =========================================================
# UNCERTAINTY VALIDATION
# =========================================================

def test_invalid_uncertainty_is_rejected():

    with pytest.raises(ValueError):

        select(
            {
                "HOME": 0.60,
                "DRAW": 0.20,
                "AWAY": 0.20,
            },
            {
                "HOME": 2.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            50_000,
            uncertainty="INVALID",
        )


# =========================================================
# ODDS VALIDATION
# =========================================================

def test_odds_must_be_greater_than_one():

    with pytest.raises(ValueError):

        select(
            {
                "HOME": 0.60,
                "DRAW": 0.20,
                "AWAY": 0.20,
            },
            {
                "HOME": 1.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            50_000,
        )


# =========================================================
# PROBABILITY VALIDATION
# =========================================================

def test_probability_must_be_between_zero_and_one():

    with pytest.raises(ValueError):

        select(
            {
                "HOME": 1.20,
                "DRAW": 0.20,
                "AWAY": 0.20,
            },
            {
                "HOME": 2.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            50_000,
        )


# =========================================================
# BANKROLL VALIDATION
# =========================================================

def test_bankroll_must_be_positive():

    with pytest.raises(ValueError):

        select(
            {
                "HOME": 0.60,
                "DRAW": 0.20,
                "AWAY": 0.20,
            },
            {
                "HOME": 2.00,
                "DRAW": 3.50,
                "AWAY": 4.00,
            },
            0,
        )


# =========================================================
# MISSING ODDS
# =========================================================

def test_missing_odds_are_not_selected():

    rows = select(
        {
            "HOME": 0.60,
            "DRAW": 0.20,
            "AWAY": 0.20,
        },
        {
            "HOME": 2.00,
        },
        50_000,
        uncertainty="LOW",
    )

    assert len(rows) == 1
    assert rows[0]["outcome"] == "HOME"


# =========================================================
# MINIMUM ODDS DOES NOT AUTOMATICALLY MEAN ELIGIBLE
# =========================================================

def test_odds_above_minimum_still_requires_ev():

    rows = select(
        {
            "HOME": 0.30,
            "DRAW": 0.35,
            "AWAY": 0.35,
        },
        {
            "HOME": 1.50,
            "DRAW": 1.60,
            "AWAY": 1.70,
        },
        50_000,
        uncertainty="HIGH",
    )

    for row in rows:

        assert row["eligible"] is False


# =========================================================
# KELLY RISK CAP
# =========================================================

def test_all_selected_stakes_respect_two_percent_cap():

    rows = select(
        {
            "HOME": 0.70,
            "DRAW": 0.20,
            "AWAY": 0.10,
        },
        {
            "HOME": 2.00,
            "DRAW": 4.00,
            "AWAY": 6.00,
        },
        50_000,
        uncertainty="LOW",
    )

    max_stake = 50_000 * 0.02

    for row in rows:

        assert row["stake"] <= max_stake


# =========================================================
# MODEL SNAPSHOT MUST REMAIN LOCKED
# =========================================================

def test_odds_cannot_change_lambda():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    original_home = pipeline.lambda_home
    original_away = pipeline.lambda_away

    pipeline.analyze_odds(
        {
            "HOME": 1.50,
            "DRAW": 5.00,
            "AWAY": 10.00,
        },
        50_000,
    )

    assert pipeline.lambda_home == pytest.approx(
        original_home
    )

    assert pipeline.lambda_away == pytest.approx(
        original_away
    )


# =========================================================
# ODDS CANNOT CHANGE MODEL PROBABILITIES
# =========================================================

def test_odds_cannot_change_model_probabilities():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    original_probabilities = (
        pipeline.probabilities.copy()
    )

    pipeline.analyze_odds(
        {
            "HOME": 1.50,
            "DRAW": 8.00,
            "AWAY": 12.00,
        },
        50_000,
    )

    assert pipeline.probabilities == (
        original_probabilities
    )


# =========================================================
# MODEL LOCK MUST SURVIVE ODDS ANALYSIS
# =========================================================

def test_model_lock_survives_odds_analysis():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    assert pipeline.model_locked is True

    pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
    )

    assert pipeline.model_locked is True


# =========================================================
# POISSON PROBABILITIES RANGE
# =========================================================

def test_poisson_probabilities_are_valid():

    probabilities = poisson_match_probabilities(
        1.5,
        1.1,
    )

    for probability in probabilities.values():

        assert probability >= 0.0
        assert probability <= 1.0


# =========================================================
# MONTE CARLO PROBABILITIES RANGE
# =========================================================

def test_monte_carlo_probabilities_are_valid():

    result = simulate_match(
        1.5,
        1.1,
        iterations=100_000,
    )

    for probability in result.values():

        assert probability >= 0.0
        assert probability <= 1.0


# =========================================================
# LAMBDA MUST BE POSITIVE
# =========================================================

def test_lambda_values_are_positive():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    home, away = calculate_lambdas(stats)

    assert home > 0
    assert away > 0


# =========================================================
# VERY HIGH MUST NEVER PRODUCE STAKE
# =========================================================

def test_very_high_uncertainty_never_produces_stake():

    rows = select(
        {
            "HOME": 0.90,
            "DRAW": 0.05,
            "AWAY": 0.05,
        },
        {
            "HOME": 5.00,
            "DRAW": 5.00,
            "AWAY": 5.00,
        },
        50_000,
        uncertainty="VERY_HIGH",
    )

    for row in rows:

        assert row["eligible"] is False
        assert row["stake"] == 0.0
        assert row["quarter_kelly"] == 0.0


# =========================================================
# BACKTEST - 1X2
# =========================================================

def test_backtest_home_win():

    result = settle_market(
        "HOME",
        2,
        1,
    )

    assert result == "WIN"


def test_backtest_home_loss():

    result = settle_market(
        "HOME",
        0,
        2,
    )

    assert result == "LOSS"


def test_backtest_draw():

    result = settle_market(
        "DRAW",
        1,
        1,
    )

    assert result == "WIN"


def test_backtest_away_win():

    result = settle_market(
        "AWAY",
        0,
        2,
    )

    assert result == "WIN"


# =========================================================
# BACKTEST - TOTAL GOALS
# =========================================================

def test_backtest_over_2_5():

    result = settle_market(
        "OVER_2.5",
        2,
        1,
    )

    assert result == "WIN"


def test_backtest_under_2_5():

    result = settle_market(
        "UNDER_2.5",
        1,
        1,
    )

    assert result == "WIN"


def test_backtest_over_2_5_loss():

    result = settle_market(
        "OVER_2.5",
        1,
        1,
    )

    assert result == "LOSS"


def test_backtest_under_2_5_loss():

    result = settle_market(
        "UNDER_2.5",
        2,
        1,
    )

    assert result == "LOSS"


# =========================================================
# BACKTEST - BTTS
# =========================================================

def test_backtest_btts_yes():

    result = settle_market(
        "BTTS_YES",
        2,
        1,
    )

    assert result == "WIN"


def test_backtest_btts_no():

    result = settle_market(
        "BTTS_NO",
        0,
        2,
    )

    assert result == "WIN"


def test_backtest_btts_yes_loss():

    result = settle_market(
        "BTTS_YES",
        2,
        0,
    )

    assert result == "LOSS"


def test_backtest_btts_no_loss():

    result = settle_market(
        "BTTS_NO",
        2,
        1,
    )

    assert result == "LOSS"


# =========================================================
# BACKTEST - CORRECT SCORE
# =========================================================

def test_backtest_correct_score():

    result = settle_market(
        "2-1",
        2,
        1,
    )

    assert result == "WIN"


def test_backtest_correct_score_loss():

    result = settle_market(
        "2-1",
        1,
        1,
    )

    assert result == "LOSS"


# =========================================================
# BACKTEST - PROFIT
# =========================================================

def test_backtest_profit_win():

    profit = calculate_profit(
        "WIN",
        100.0,
        2.0,
    )

    assert profit == 100.0


def test_backtest_profit_loss():

    profit = calculate_profit(
        "LOSS",
        100.0,
        2.0,
    )

    assert profit == -100.0


def test_backtest_profit_void():

    profit = calculate_profit(
        "VOID",
        100.0,
        2.0,
    )

    assert profit == 0.0


# =========================================================
# BACKTEST - SINGLE BET
# =========================================================

def test_backtest_settle_bet():

    result = settle_bet(
        outcome="HOME",
        odds=2.0,
        stake=100.0,
        home_goals=2,
        away_goals=1,
    )

    assert result.settlement == "WIN"
    assert result.profit == 100.0
    assert result.stake == 100.0
    assert result.outcome == "HOME"


# =========================================================
# BACKTEST - ENGINE SUMMARY
# =========================================================

def test_backtest_engine_summary():

    engine = BacktestEngine(
        starting_bankroll=1000.0
    )

    engine.add_bet(
        outcome="HOME",
        odds=2.0,
        stake=100.0,
        home_goals=2,
        away_goals=1,
    )

    engine.add_bet(
        outcome="HOME",
        odds=2.0,
        stake=100.0,
        home_goals=0,
        away_goals=1,
    )

    summary = engine.summary()

    assert summary.total_bets == 2
    assert summary.wins == 1
    assert summary.losses == 1
    assert summary.voids == 0

    assert summary.total_stake == 200.0
    assert summary.total_profit == 0.0

    assert summary.roi == 0.0
    assert summary.hit_rate == 0.5

    assert summary.starting_bankroll == 1000.0
    assert summary.ending_bankroll == 1000.0


# =========================================================
# BACKTEST - NON ELIGIBLE SELECTION
# =========================================================

def test_backtest_only_eligible_selection():

    engine = BacktestEngine()

    selection = {
        "outcome": "HOME",
        "probability": 0.60,
        "odds": 2.0,
        "ev": 0.20,
        "eligible": False,
        "stake": 0.0,
    }

    result = engine.add_selection(
        selection,
        home_goals=2,
        away_goals=1,
    )

    assert result is None
    assert len(engine.records) == 0


# =========================================================
# BACKTEST - ELIGIBLE SELECTION
# =========================================================

def test_backtest_eligible_selection():

    engine = BacktestEngine()

    selection = {
        "outcome": "HOME",
        "probability": 0.60,
        "odds": 2.0,
        "ev": 0.20,
        "eligible": True,
        "stake": 100.0,
    }

    result = engine.add_selection(
        selection,
        home_goals=2,
        away_goals=1,
    )

    assert result is not None
    assert result.settlement == "WIN"
    assert result.profit == 100.0


# =========================================================
# BACKTEST - BATCH
# =========================================================

def test_run_backtest():

    selections = [
        {
            "outcome": "HOME",
            "odds": 2.0,
            "stake": 100.0,
            "eligible": True,
        },
        {
            "outcome": "DRAW",
            "odds": 3.5,
            "stake": 100.0,
            "eligible": True,
        },
    ]

    summary = run_backtest(
        selections,
        home_goals=2,
        away_goals=1,
        starting_bankroll=1000.0,
    )

    assert summary.total_bets == 2
    assert summary.wins == 1
    assert summary.losses == 1
    assert summary.voids == 0

    # HOME 2.00 kazanır: +100
    # DRAW 3.50 kaybeder: -100
    # Toplam: 0
    assert summary.total_profit == 0.0

    assert summary.total_stake == 200.0
    assert summary.roi == 0.0
    assert summary.hit_rate == 0.5
    assert summary.ending_bankroll == 1000.0


# =========================================================
# BACKTEST - VALIDATION
# =========================================================

def test_backtest_rejects_negative_goals():

    with pytest.raises(ValueError):

        settle_market(
            "HOME",
            -1,
            0,
        )


def test_backtest_rejects_invalid_market():

    with pytest.raises(ValueError):

        settle_market(
            "INVALID_MARKET",
            1,
            0,
        )


def test_backtest_rejects_invalid_odds():

    with pytest.raises(ValueError):

        calculate_profit(
            "WIN",
            100.0,
            1.0,
        )


def test_backtest_rejects_negative_stake():

    with pytest.raises(ValueError):

        calculate_profit(
            "WIN",
            -100.0,
            2.0,
        )


def test_backtest_rejects_negative_starting_bankroll():

    with pytest.raises(ValueError):

        BacktestEngine(
            starting_bankroll=-100.0
        )


# =========================================================
# PIPELINE - STRESS TEST INTEGRATION
# =========================================================

def test_pipeline_stress_test_returns_all_scenarios():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    result = pipeline.stress_test()

    assert "lambdas" in result
    assert "probabilities" in result

    assert set(
        result["lambdas"].keys()
    ) == {
        "OPTIMISTIC",
        "BASELINE",
        "PESSIMISTIC",
    }

    assert set(
        result["probabilities"].keys()
    ) == {
        "OPTIMISTIC",
        "BASELINE",
        "PESSIMISTIC",
    }


# =========================================================
# PIPELINE - STRESS LAMBDA INTEGRITY
# =========================================================

def test_pipeline_stress_lambdas_are_based_on_locked_model():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    original_home = pipeline.lambda_home
    original_away = pipeline.lambda_away

    result = pipeline.stress_test()

    baseline = result["lambdas"]["BASELINE"]

    assert baseline["lambda_home"] == pytest.approx(
        original_home
    )

    assert baseline["lambda_away"] == pytest.approx(
        original_away
    )


# =========================================================
# PIPELINE - STRESS DOES NOT CHANGE MODEL
# =========================================================

def test_stress_test_cannot_change_locked_model():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    snapshot_before = pipeline.snapshot

    pipeline.stress_test()

    assert pipeline.snapshot == snapshot_before
    assert pipeline.snapshot.locked is True


# =========================================================
# PIPELINE - STRESS PROBABILITIES ARE VALID
# =========================================================

def test_stress_probabilities_are_valid():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    result = pipeline.stress_test()

    for scenario, probabilities in (
        result["probabilities"].items()
    ):

        assert scenario in {
            "OPTIMISTIC",
            "BASELINE",
            "PESSIMISTIC",
        }

        assert probabilities

        for probability in probabilities.values():

            assert probability >= 0.0
            assert probability <= 1.0


# =========================================================
# PIPELINE - FULL ANALYSIS RESULT
# =========================================================

def test_pipeline_full_analysis_result():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    result = pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
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

    assert isinstance(
        result.selections,
        list,
    )


# =========================================================
# PIPELINE - FAIR ODDS
# =========================================================

def test_pipeline_fair_odds_are_inverse_of_model_probability():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    result = pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
    )

    for outcome, probability in (
        pipeline.probabilities.items()
    ):

        if probability <= 0:
            continue

        assert result.fair_odds[outcome] == pytest.approx(
            1.0 / probability
        )


# =========================================================
# PIPELINE - BASELINE EV
# =========================================================

def test_pipeline_baseline_ev_uses_locked_model_probability():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    odds = {
        "HOME": 2.00,
        "DRAW": 3.50,
        "AWAY": 4.00,
    }

    result = pipeline.analyze_odds(
        odds,
        50_000,
    )

    for outcome, odd in odds.items():

        expected = (
            pipeline.probabilities[outcome]
            * odd
            - 1.0
        )

        assert result.ev[outcome] == pytest.approx(
            expected
        )


# =========================================================
# PIPELINE - PESSIMISTIC EV
# =========================================================

def test_pipeline_pessimistic_ev_uses_pessimistic_probability():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    odds = {
        "HOME": 2.00,
        "DRAW": 3.50,
        "AWAY": 4.00,
    }

    result = pipeline.analyze_odds(
        odds,
        50_000,
    )

    for outcome, odd in odds.items():

        expected = (
            result.pessimistic_probabilities[outcome]
            * odd
            - 1.0
        )

        assert result.pessimistic_ev[outcome] == pytest.approx(
            expected
        )


# =========================================================
# PIPELINE - ODDS CANNOT CHANGE STRESS MODEL
# =========================================================

def test_different_odds_cannot_change_stress_results():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    stress_before = pipeline.stress_test()

    pipeline.analyze_odds(
        {
            "HOME": 1.50,
            "DRAW": 6.00,
            "AWAY": 10.00,
        },
        50_000,
    )

    stress_after = pipeline.stress_test()

    assert stress_after == stress_before


# =========================================================
# PIPELINE - ODDS CANNOT CHANGE PESSIMISTIC PROBABILITIES
# =========================================================

def test_different_odds_cannot_change_pessimistic_probabilities():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    first = pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
    )

    first_pessimistic = (
        first.pessimistic_probabilities.copy()
    )

    second = pipeline.analyze_odds(
        {
            "HOME": 5.00,
            "DRAW": 2.00,
            "AWAY": 8.00,
        },
        50_000,
    )

    second_pessimistic = (
        second.pessimistic_probabilities.copy()
    )

    assert second_pessimistic == (
        first_pessimistic
    )


# =========================================================
# PIPELINE - MODEL LOCK AFTER COMPLETE FLOW
# =========================================================

def test_model_lock_survives_complete_pipeline():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    original_snapshot = pipeline.snapshot

    pipeline.stress_test()

    pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
        uncertainty="MEDIUM",
    )

    assert pipeline.snapshot == original_snapshot
    assert pipeline.snapshot.locked is True
    assert pipeline.model_locked is True


# =========================================================
# PIPELINE - VERY HIGH UNCERTAINTY
# =========================================================

def test_pipeline_very_high_uncertainty_produces_no_bet():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    result = pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
        uncertainty="VERY_HIGH",
    )

    assert len(result.selections) == 3

    for selection in result.selections:

        assert selection["eligible"] is False
        assert selection["stake"] == 0.0
        assert selection["quarter_kelly"] == 0.0


# =========================================================
# PIPELINE - BANKROLL CAP
# =========================================================

def test_pipeline_selected_stakes_respect_two_percent_cap():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    result = pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 4.00,
            "AWAY": 6.00,
        },
        50_000,
        uncertainty="LOW",
    )

    maximum_stake = 50_000 * 0.02

    for selection in result.selections:

        assert selection["stake"] <= (
            maximum_stake
        )


# =========================================================
# PIPELINE - CONVENIENCE FLOW
# =========================================================

def test_pipeline_complete_result_contains_locked_snapshot():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    result = pipeline.analyze_odds(
        {
            "HOME": 2.00,
            "DRAW": 3.50,
            "AWAY": 4.00,
        },
        50_000,
    )

    assert result.snapshot is pipeline.snapshot
    assert result.snapshot.locked is True
    assert result.snapshot.model_version == "Q200-V3.1"


# =========================================================
# PIPELINE - INVALID ODDS
# =========================================================

def test_pipeline_rejects_invalid_odds():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    with pytest.raises(ValueError):

        pipeline.analyze_odds(
            {
                "HOME": 1.0,
                "DRAW": 3.5,
                "AWAY": 4.0,
            },
            50_000,
        )


# =========================================================
# PIPELINE - INVALID BANKROLL
# =========================================================

def test_pipeline_rejects_invalid_bankroll():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    with pytest.raises(ValueError):

        pipeline.analyze_odds(
            {
                "HOME": 2.0,
                "DRAW": 3.5,
                "AWAY": 4.0,
            },
            0,
        )


# =========================================================
# PIPELINE - EMPTY ODDS
# =========================================================

def test_pipeline_rejects_empty_odds():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    with pytest.raises(ValueError):

        pipeline.analyze_odds(
            {},
            50_000,
        )


# =========================================================
# PIPELINE - ODDS TYPE VALIDATION
# =========================================================

def test_pipeline_rejects_non_dict_odds():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    with pytest.raises(TypeError):

        pipeline.analyze_odds(
            ["HOME", 2.0],
            50_000,
        )


# =========================================================
# PIPELINE - UNCERTAINTY VALIDATION
# =========================================================

def test_pipeline_rejects_invalid_uncertainty():

    stats = TeamStats(
        2.0,
        1.2,
        1.5,
        1.8,
        1.1,
        1.0,
        1.4,
    )

    pipeline = Q200Pipeline(stats)

    with pytest.raises(ValueError):

        pipeline.analyze_odds(
            {
                "HOME": 2.0,
                "DRAW": 3.5,
                "AWAY": 4.0,
            },
            50_000,
            uncertainty="INVALID",
        )
