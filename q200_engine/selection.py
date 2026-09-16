"""
Q200 Engine - Selection Layer

Q200 V3.1
"""

from __future__ import annotations

from .kelly import quarter_kelly
from .odds import expected_value


MINIMUM_ODDS = 1.50

EV_THRESHOLDS = {
    "LOW": 0.05,
    "MEDIUM": 0.08,
    "HIGH": 0.12,
}


def select(
    probabilities: dict[str, float],
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> list[dict]:

    uncertainty = uncertainty.upper()

    if uncertainty == "VERY_HIGH":
        return [
            {
                "outcome": outcome,
                "odds": odds.get(outcome),
                "probability": probabilities.get(outcome),
                "eligible": False,
                "reason": "VERY_HIGH uncertainty -> NO BET",
            }
            for outcome in probabilities
        ]

    if uncertainty not in EV_THRESHOLDS:
        raise ValueError(
            "uncertainty LOW, MEDIUM, HIGH veya VERY_HIGH olmalıdır."
        )

    threshold = EV_THRESHOLDS[uncertainty]

    rows = []

    for outcome, probability in probabilities.items():

        if outcome not in odds:
            continue

        odd = odds[outcome]

        ev = expected_value(
            probability,
            odd,
        )

        eligible = (
            odd >= MINIMUM_ODDS
            and ev >= threshold
        )

        kelly = quarter_kelly(
            probability,
            odd,
            bankroll,
        )

        rows.append({
            "outcome": outcome,
            "probability": probability,
            "odds": odd,
            "ev": ev,
            "eligible": eligible,
            "stake": kelly["stake"],
            "quarter_kelly": kelly["quarter_kelly"],
            "reason": (
                "ELIGIBLE"
                if eligible
                else "FILTERED"
            ),
        })

    rows.sort(
        key=lambda x: (
            x["eligible"],
            x["ev"],
            x["probability"],
        ),
        reverse=True,
    )

    if not rows:
        raise ValueError(
            "Geçerli selection bulunamadı."
        )

    # Minimum odds filtresi için özel davranış:
    # Hiçbir oran minimum 1.50'yi geçmiyorsa hata.
    if all(
        row["odds"] < MINIMUM_ODDS
        for row in rows
    ):
        raise ValueError(
            "Minimum odds filter: tüm oranlar 1.50 altında."
        )

    return rows
