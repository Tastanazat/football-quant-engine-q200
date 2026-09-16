"""
Q200 Engine - Monte Carlo Layer

Stage 2:
Model -> Monte Carlo

KRİTİK KURALLAR:
- Odds kullanılmaz.
- Minimum 100.000 iterasyon.
- Lambda negatif olamaz.
- Sonuçlar HOME / DRAW / AWAY olarak döner.
"""

from __future__ import annotations

import math
import random
from typing import Dict


MIN_ITERATIONS = 100_000


def _sample_poisson(lam: float) -> int:
    """
    Poisson dağılımından tek örnek üretir.

    NumPy kullanılmaz.
    """

    if lam < 0:
        raise ValueError(
            "Lambda cannot be negative."
        )

    # Knuth algorithm
    limit = math.exp(-lam)

    k = 0
    product = 1.0

    while product > limit:
        k += 1
        product *= random.random()

    return k - 1


def simulate_match(
    lambda_home: float,
    lambda_away: float,
    iterations: int = MIN_ITERATIONS,
) -> Dict[str, float]:
    """
    Monte Carlo maç simülasyonu.

    Parameters
    ----------
    lambda_home:
        Home takım gol beklentisi.

    lambda_away:
        Away takım gol beklentisi.

    iterations:
        Simülasyon sayısı.
        Minimum 100.000 olmalıdır.

    Returns
    -------
    Dict[str, float]
        HOME / DRAW / AWAY olasılıkları.
    """

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if iterations < MIN_ITERATIONS:
        raise ValueError(
            "Monte Carlo requires at least "
            f"{MIN_ITERATIONS} iterations."
        )

    if lambda_home < 0:
        raise ValueError(
            "lambda_home cannot be negative."
        )

    if lambda_away < 0:
        raise ValueError(
            "lambda_away cannot be negative."
        )

    # -----------------------------------------------------
    # COUNTERS
    # -----------------------------------------------------

    home_wins = 0
    draws = 0
    away_wins = 0

    # -----------------------------------------------------
    # SIMULATION
    # -----------------------------------------------------

    for _ in range(iterations):

        home_goals = _sample_poisson(
            lambda_home
        )

        away_goals = _sample_poisson(
            lambda_away
        )

        if home_goals > away_goals:

            home_wins += 1

        elif home_goals == away_goals:

            draws += 1

        else:

            away_wins += 1

    # -----------------------------------------------------
    # TOTAL
    # -----------------------------------------------------

    total = (
        home_wins
        + draws
        + away_wins
    )

    if total <= 0:
        raise RuntimeError(
            "Monte Carlo produced no valid simulations."
        )

    # -----------------------------------------------------
    # PROBABILITIES
    # -----------------------------------------------------

    probabilities = {
        "HOME": home_wins / total,
        "DRAW": draws / total,
        "AWAY": away_wins / total,
    }

    return probabilities
