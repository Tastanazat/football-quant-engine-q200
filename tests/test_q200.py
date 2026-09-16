import pytest

from q200_engine.schema import TeamStats
from q200_engine.model import calculate_lambdas, build_model
from q200_engine.poisson_model import poisson_match_probabilities
from q200_engine.monte_carlo import simulate_match
from q200_engine.odds import implied_probabilities
from q200_engine.selection import select
from q200_engine.kelly import quarter_kelly


# =========================================================
# LAMBDA FORMULA
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

    # Q200 V3.1
    # HOME:
    # 0.35*2.0 + 0.35*1.8 + 0.15*1.1 + 0.15*1.4
    # = 1.705
    assert h == pytest.approx(1.705)

    # Legacy 7-parametreli TeamStats yapısında
    # AWAY lambda:
    # 0.35*1.5 + 0.35*1.2 + 0.15*1.0
    # = 1.095
    assert a == pytest.approx(1.095)


# =========================================================
# PROBABILITIES
# =========================================================

def test_probabilities_sum_to_one():
    p = poisson_match_probabilities(
        1.5,
        1.1,
    )

    assert sum(p.values()) == pytest.approx(
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
# NO-VIG
# =========================================================

def test_no_vig_sums_to_one():
    p = implied_probabilities(
        {
            "HOME": 2.0,
            "DRAW": 3.5,
            "AWAY": 4.0,
        }
    )

    assert sum(p.values()) == pytest.approx(1.0)


# =========================================================
# QUARTER KELLY
# =========================================================

def test_quarter_kelly_respects_two_percent_cap():
    result = quarter_kelly(
        0.70,
        2.0,
        50_000,
    )

    # Maximum bankroll risk = 2%
    # 50,000 * 0.02 = 1,000 TL
    assert result["stake"] <= 1000


# =========================================================
# MINIMUM ODDS FILTER
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
                "DRAW": 4.0,
                "AWAY": 5.0,
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
# MODEL INDEPENDENCE FROM ODDS
# =========================================================

def test_pipeline_keeps_model_independent_of_odds():
    from q200_engine.pipeline import Q200Pipeline

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
