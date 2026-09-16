"""
Q200 Engine - Kelly

Q200 V3.1

Maximum bankroll risk:
%2

Quarter Kelly:
%25 Kelly
"""

from __future__ import annotations


MAX_BANKROLL_RISK = 0.02
QUARTER_KELLY = 0.25


def quarter_kelly(
    probability: float,
    odds: float,
    bankroll: float,
) -> dict[str, float]:

    if not 0 <= probability <= 1:
        raise ValueError(
            "Probability 0-1 arasında olmalıdır."
        )

    if odds <= 1:
        raise ValueError(
            "Odds 1'den büyük olmalıdır."
        )

    if bankroll <= 0:
        raise ValueError(
            "Bankroll pozitif olmalıdır."
        )

    b = odds - 1.0

    q = 1.0 - probability

    full_kelly = (
        (b * probability - q) / b
    )

    if full_kelly < 0:
        full_kelly = 0.0

    quarter = (
        full_kelly
        * QUARTER_KELLY
    )

    max_stake = (
        bankroll
        * MAX_BANKROLL_RISK
    )

    stake = min(
        bankroll * quarter,
        max_stake,
    )

    return {
        "full_kelly": full_kelly,
        "quarter_kelly": quarter,
        "stake": stake,
        "risk_cap": max_stake,
    }
