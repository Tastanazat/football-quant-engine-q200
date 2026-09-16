"""
Q200 Selection Engine

Selection is performed only AFTER the model is locked.

Rules:
- Minimum odds: 1.50
- EV threshold depends on uncertainty
- Very high uncertainty => NO BET
- Odds do not influence model probabilities
"""

from __future__ import annotations

from typing import Any, Dict, List


MIN_ODDS = 1.50

EV_THRESHOLDS = {
    "LOW": 0.05,
    "MEDIUM": 0.08,
    "HIGH": 0.12,
    "VERY_HIGH": float("inf"),
}


def _normalize_uncertainty(uncertainty: str) -> str:
    """Normalize uncertainty level."""

    value = str(uncertainty).strip().upper().replace(" ", "_")

    aliases = {
        "VERYHIGH": "VERY_HIGH",
        "VERY_HIGH": "VERY_HIGH",
        "VERY-HIGH": "VERY_HIGH",
        "ÇOK_YÜKSEK": "VERY_HIGH",
        "COK_YUKSEK": "VERY_HIGH",
    }

    return aliases.get(value, value)


def _ev(probability: float, odds: float) -> float:
    """
    Expected value.

    EV = probability * odds - 1
    """

    return float(probability) * float(odds) - 1.0


def select(
    probabilities: Dict[str, float],
    odds: Dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
    min_odds: float = MIN_ODDS,
) -> List[Dict[str, Any]]:
    """
    Select eligible betting opportunities.

    Parameters
    ----------
    probabilities:
        Model probabilities, e.g.
        {"HOME": 0.60, "DRAW": 0.20, "AWAY": 0.20}

    odds:
        Market odds, e.g.
        {"HOME": 2.00, "DRAW": 4.00, "AWAY": 5.00}

    bankroll:
        Current bankroll.

    uncertainty:
        LOW / MEDIUM / HIGH / VERY_HIGH

    min_odds:
        Minimum acceptable odds. Default = 1.50.

    Returns
    -------
    List of eligible selections.
    """

    if not isinstance(probabilities, dict):
        raise TypeError("probabilities must be a dictionary")

    if not isinstance(odds, dict):
        raise TypeError("odds must be a dictionary")

    if bankroll <= 0:
        raise ValueError("bankroll must be greater than zero")

    uncertainty = _normalize_uncertainty(uncertainty)

    if uncertainty not in EV_THRESHOLDS:
        raise ValueError(
            "uncertainty must be LOW, MEDIUM, HIGH or VERY_HIGH"
        )

    threshold = EV_THRESHOLDS[uncertainty]

    # VERY_HIGH uncertainty = NO BET
    if threshold == float("inf"):
        return []

    selections: List[Dict[str, Any]] = []

    for market, probability in probabilities.items():

        if market not in odds:
            continue

        try:
            probability = float(probability)
            market_odds = float(odds[market])
        except (TypeError, ValueError):
            continue

        if probability < 0 or probability > 1:
            continue

        # Minimum odds filter
        if market_odds < min_odds:
            continue

        ev = _ev(probability, market_odds)

        # EV threshold
        if ev < threshold:
            continue

        # Quarter Kelly
        q = market_odds - 1.0

        if q <= 0:
            continue

        kelly = ((probability * market_odds) - 1.0) / q

        if kelly < 0:
            kelly = 0.0

        quarter_kelly = kelly * 0.25

        # Maximum bankroll risk = 2%
        bankroll_fraction = min(quarter_kelly, 0.02)

        stake = bankroll * bankroll_fraction

        selections.append(
            {
                "market": market,
                "probability": probability,
                "odds": market_odds,
                "ev": ev,
                "uncertainty": uncertainty,
                "kelly": kelly,
                "quarter_kelly": quarter_kelly,
                "bankroll_fraction": bankroll_fraction,
                "stake": stake,
                "eligible": True,
            }
        )

    return selections


def minimum_odds_filter(
    probabilities: Dict[str, float],
    odds: Dict[str, float],
    min_odds: float = MIN_ODDS,
) -> Dict[str, float]:
    """
    Return only markets whose odds satisfy the minimum odds rule.
    """

    result: Dict[str, float] = {}

    for market, market_odds in odds.items():

        try:
            market_odds = float(market_odds)
        except (TypeError, ValueError):
            continue

        if market_odds >= min_odds and market in probabilities:
            result[market] = market_odds

    return result


def calculate_ev(
    probability: float,
    odds: float,
) -> float:
    """Public EV calculation helper."""

    return _ev(probability, odds)


def has_value(
    probability: float,
    odds: float,
    uncertainty: str = "MEDIUM",
) -> bool:
    """Check whether a single selection passes the EV threshold."""

    uncertainty = _normalize_uncertainty(uncertainty)

    if uncertainty not in EV_THRESHOLDS:
        raise ValueError(
            "uncertainty must be LOW, MEDIUM, HIGH or VERY_HIGH"
        )

    if float(odds) < MIN_ODDS:
        return False

    threshold = EV_THRESHOLDS[uncertainty]

    if threshold == float("inf"):
        return False

    return _ev(probability, odds) >= threshold


__all__ = [
    "MIN_ODDS",
    "EV_THRESHOLDS",
    "select",
    "minimum_odds_filter",
    "calculate_ev",
    "has_value",
]
