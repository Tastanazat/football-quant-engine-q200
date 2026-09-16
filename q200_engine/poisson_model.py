"""
Q200 Engine - Poisson Model

Q200 V3.1
"""

from __future__ import annotations

import math


# =========================================================
# POISSON PMF
# =========================================================

def poisson_pmf(k: int, lam: float) -> float:
    if k < 0:
        raise ValueError("k negatif olamaz.")

    if lam < 0:
        raise ValueError("lambda negatif olamaz.")

    if lam == 0:
        return 1.0 if k == 0 else 0.0

    return (
        math.exp(-lam)
        * (lam ** k)
        / math.factorial(k)
    )


# =========================================================
# SCORE MATRIX
# =========================================================

def poisson_score_matrix(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> list[list[float]]:

    if lambda_home < 0:
        raise ValueError(
            "lambda_home negatif olamaz."
        )

    if lambda_away < 0:
        raise ValueError(
            "lambda_away negatif olamaz."
        )

    if max_goals < 1:
        raise ValueError(
            "max_goals en az 1 olmalıdır."
        )

    home_probs = [
        poisson_pmf(i, lambda_home)
        for i in range(max_goals + 1)
    ]

    away_probs = [
        poisson_pmf(i, lambda_away)
        for i in range(max_goals + 1)
    ]

    matrix = []

    for h in range(max_goals + 1):
        row = []

        for a in range(max_goals + 1):
            row.append(
                home_probs[h] * away_probs[a]
            )

        matrix.append(row)

    return matrix


# =========================================================
# MATCH PROBABILITIES
# =========================================================

def poisson_match_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> dict[str, float]:

    matrix = poisson_score_matrix(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    home = 0.0
    draw = 0.0
    away = 0.0

    for h in range(max_goals + 1):
        for a in range(max_goals + 1):

            probability = matrix[h][a]

            if h > a:
                home += probability

            elif h == a:
                draw += probability

            else:
                away += probability

    total = home + draw + away

    if total <= 0:
        raise ValueError(
            "Poisson olasılık toplamı geçersiz."
        )

    return {
        "HOME": home / total,
        "DRAW": draw / total,
        "AWAY": away / total,
    }
