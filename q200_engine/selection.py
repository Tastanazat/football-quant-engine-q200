from typing import Dict, List, Any


MIN_ODDS = 1.50

EV_THRESHOLDS = {
    "LOW": 0.05,
    "MEDIUM": 0.08,
    "HIGH": 0.12,
}


def select(
    probabilities: Dict[str, float],
    odds: Dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> List[Dict[str, Any]]:
    """
    Q200 selection engine.

    Parameters
    ----------
    probabilities:
        Model probabilities, e.g.
        {"HOME": 0.60, "DRAW": 0.20, "AWAY": 0.20}

    odds:
        Market odds, e.g.
        {"HOME": 2.0, "DRAW": 4.0, "AWAY": 5.0}

    bankroll:
        Current bankroll.

    uncertainty:
        LOW / MEDIUM / HIGH

    Returns
    -------
    List of eligible selections.
    """

    if bankroll <= 0:
        raise ValueError("bankroll must be greater than 0")

    uncertainty = str(uncertainty).upper()

    if uncertainty not in EV_THRESHOLDS:
        raise ValueError(
            "uncertainty must be LOW, MEDIUM or HIGH"
        )

    if not isinstance(probabilities, dict):
        raise TypeError("probabilities must be a dictionary")

    if not isinstance(odds, dict):
        raise TypeError("odds must be a dictionary")

    # Minimum odds filter
    for outcome, odd in odds.items():
        if odd < MIN_ODDS:
            raise ValueError(
                f"Minimum odds is {MIN_ODDS:.2f}: "
                f"{outcome}={odd}"
            )

    selections = []

    min_ev = EV_THRESHOLDS[uncertainty]

    for outcome, probability in probabilities.items():

        if outcome not in odds:
            continue

        odd = float(odds[outcome])
        probability = float(probability)

        if probability <= 0:
            continue

        if probability > 1:
            raise ValueError(
                f"Probability must be between 0 and 1: {outcome}"
            )

        # Fair odds
        fair_odds = 1.0 / probability

        # Expected Value
        ev = (probability * odd) - 1.0

        # Value percentage
        value = ev * 100.0

        eligible = ev >= min_ev

        row = {
            "outcome": outcome,
            "probability": probability,
            "odds": odd,
            "fair_odds": fair_odds,
            "ev": ev,
            "value": value,
            "uncertainty": uncertainty,
            "eligible": eligible,
            "bankroll": bankroll,
        }

        if eligible:
            selections.append(row)

    # Highest EV first
    selections.sort(
        key=lambda x: x["ev"],
        reverse=True
    )

    return selections
