"""
Q200 Engine - Odds Layer

Q200 V3.1
"""

from __future__ import annotations


# =========================================================
# IMPLIED PROBABILITIES
# =========================================================

def implied_probabilities(
    odds: dict[str, float],
) -> dict[str, float]:

    if not odds:
        raise ValueError(
            "Odds boş olamaz."
        )

    for outcome, odd in odds.items():

        if odd <= 1.0:
            raise ValueError(
                f"{outcome} oranı 1.00'dan büyük olmalıdır."
            )

    raw = {
        outcome: 1.0 / odd
        for outcome, odd in odds.items()
    }

    total = sum(raw.values())

    if total <= 0:
        raise ValueError(
            "Implied probability toplamı geçersiz."
        )

    return {
        outcome: probability / total
        for outcome, probability in raw.items()
    }


# =========================================================
# FAIR ODDS
# =========================================================

def fair_odds(
    probabilities: dict[str, float],
) -> dict[str, float]:

    result = {}

    for outcome, probability in probabilities.items():

        if probability <= 0:
            result[outcome] = float("inf")

        else:
            result[outcome] = 1.0 / probability

    return result


# =========================================================
# EV
# =========================================================

def expected_value(
    probability: float,
    odds: float,
) -> float:

    if probability < 0 or probability > 1:
        raise ValueError(
            "Probability 0 ile 1 arasında olmalıdır."
        )

    if odds <= 1:
        raise ValueError(
            "Odds 1'den büyük olmalıdır."
        )

    return (
        probability * odds
        - 1.0
    )
