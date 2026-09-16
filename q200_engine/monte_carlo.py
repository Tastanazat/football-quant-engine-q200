"""
Q200 Engine - Monte Carlo

Q200 V3.1
"""

from __future__ import annotations

import random

from .poisson_model import poisson_pmf


# =========================================================
# POISSON RANDOM
# =========================================================

def _sample_poisson(lam: float) -> int:
    """
    Knuth algoritması.
    """

    if lam < 0:
        raise ValueError(
            "lambda negatif olamaz."
        )

    if lam == 0:
        return 0

    limit = pow(2.718281828459045, -lam)

    product = 1.0
    k = 0

    while product > limit:
        k += 1
        product *= random.random()

    return k - 1


# =========================================================
# SIMULATION
# =========================================================

def simulate_match(
    lambda_home: float,
    lambda_away: float,
    iterations: int = 100_000,
) -> dict[str, float]:

    if iterations < 100_000:
        raise ValueError(
            "Monte Carlo minimum 100000 iteration olmalıdır."
        )

    if lambda_home < 0 or lambda_away < 0:
        raise ValueError(
            "lambda değerleri negatif olamaz."
        )

    home_wins = 0
    draws = 0
    away_wins = 0

    for _ in range(iterations):

        home_goals = _sample_poisson(lambda_home)
        away_goals = _sample_poisson(lambda_away)

        if home_goals > away_goals:
            home_wins += 1

        elif home_goals == away_goals:
            draws += 1

        else:
            away_wins += 1

    return {
        "HOME": home_wins / iterations,
        "DRAW": draws / iterations,
        "AWAY": away_wins / iterations,
    }
