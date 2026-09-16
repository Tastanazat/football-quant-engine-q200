"""
Q200 Engine - Selection Layer

Q200 V3.1

Akış:

MODEL PROBABILITIES
        ↓
ODDS
        ↓
EV
        ↓
MINIMUM ODDS
        ↓
UNCERTAINTY THRESHOLD
        ↓
KELLY
        ↓
BANKROLL RISK
        ↓
SELECTION / NO BET
"""

from __future__ import annotations

from math import isfinite

from .kelly import quarter_kelly
from .odds import expected_value


# =========================================================
# CONSTANTS
# =========================================================

MINIMUM_ODDS = 1.50

EV_THRESHOLDS = {
    "LOW": 0.05,
    "MEDIUM": 0.08,
    "HIGH": 0.12,
}

VALID_UNCERTAINTY = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "VERY_HIGH",
}


# =========================================================
# VALIDATION
# =========================================================

def _validate_probability(
    probability: float,
    outcome: str,
) -> float:
    """
    Model olasılığını doğrular.

    Beklenen aralık:
        0.0 <= probability <= 1.0
    """

    try:
        value = float(probability)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid probability for {outcome}: "
            f"{probability}"
        )

    if not isfinite(value):
        raise ValueError(
            f"Probability must be finite for {outcome}"
        )

    if value < 0.0 or value > 1.0:
        raise ValueError(
            f"Probability must be between 0 and 1 "
            f"for {outcome}"
        )

    return value


def _validate_odds(
    odd: float,
    outcome: str,
) -> float:
    """
    Odds değerini doğrular.
    """

    try:
        value = float(odd)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid odds for {outcome}: {odd}"
        )

    if not isfinite(value):
        raise ValueError(
            f"Odds must be finite for {outcome}"
        )

    if value <= 1.0:
        raise ValueError(
            f"Odds must be greater than 1.0 "
            f"for {outcome}"
        )

    return value


def _validate_bankroll(
    bankroll: float,
) -> float:
    """
    Bankroll değerini doğrular.
    """

    try:
        value = float(bankroll)
    except (TypeError, ValueError):
        raise ValueError(
            "bankroll must be numeric"
        )

    if not isfinite(value):
        raise ValueError(
            "bankroll must be finite"
        )

    if value <= 0:
        raise ValueError(
            "bankroll must be greater than zero"
        )

    return value


def _normalize_uncertainty(
    uncertainty: str,
) -> str:
    """
    Belirsizlik seviyesini normalize eder.
    """

    if not isinstance(
        uncertainty,
        str,
    ):
        raise TypeError(
            "uncertainty must be a string"
        )

    value = (
        uncertainty
        .strip()
        .upper()
    )

    if value not in VALID_UNCERTAINTY:
        raise ValueError(
            "uncertainty LOW, MEDIUM, HIGH "
            "veya VERY_HIGH olmalıdır."
        )

    return value


# =========================================================
# SELECTION
# =========================================================

def select(
    probabilities: dict[str, float],
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> list[dict]:
    """
    Q200 V3.1 selection motoru.

    Kurallar:

        Minimum Odds = 1.50

        LOW:
            EV >= +5%

        MEDIUM:
            EV >= +8%

        HIGH:
            EV >= +12%

        VERY_HIGH:
            NO BET

    Kelly yalnızca geçerli seçimler için hesaplanır.

    ÖNEMLİ:
        Bu fonksiyon model olasılıklarını değiştirmez.
    """

    # =====================================================
    # INPUT VALIDATION
    # =====================================================

    if not isinstance(
        probabilities,
        dict,
    ):
        raise TypeError(
            "probabilities must be a dictionary"
        )

    if not isinstance(
        odds,
        dict,
    ):
        raise TypeError(
            "odds must be a dictionary"
        )

    if not probabilities:
        raise ValueError(
            "probabilities cannot be empty"
        )

    if not odds:
        raise ValueError(
            "odds cannot be empty"
        )

    validated_bankroll = _validate_bankroll(
        bankroll
    )

    uncertainty = _normalize_uncertainty(
        uncertainty
    )

    # =====================================================
    # VERY HIGH UNCERTAINTY
    # =====================================================

    if uncertainty == "VERY_HIGH":

        rows = []

        for outcome, probability in probabilities.items():

            validated_probability = (
                _validate_probability(
                    probability,
                    outcome,
                )
            )

            odd = odds.get(outcome)

            validated_odd = None

            if odd is not None:
                validated_odd = _validate_odds(
                    odd,
                    outcome,
                )

            rows.append({
                "outcome": outcome,
                "odds": validated_odd,
                "probability": validated_probability,
                "ev": None,
                "eligible": False,
                "stake": 0.0,
                "quarter_kelly": 0.0,
                "reason": (
                    "VERY_HIGH uncertainty -> NO BET"
                ),
            })

        return rows

    # =====================================================
    # EV THRESHOLD
    # =====================================================

    threshold = EV_THRESHOLDS[
        uncertainty
    ]

    rows = []

    # =====================================================
    # PROCESS OUTCOMES
    # =====================================================

    for outcome, probability in probabilities.items():

        validated_probability = (
            _validate_probability(
                probability,
                outcome,
            )
        )

        # -------------------------------------------------
        # ODDS YOKSA BU MARKET ANALİZ EDİLMEZ
        # -------------------------------------------------

        if outcome not in odds:
            continue

        odd = _validate_odds(
            odds[outcome],
            outcome,
        )

        # -------------------------------------------------
        # EV
        # -------------------------------------------------

        ev = expected_value(
            validated_probability,
            odd,
        )

        # -------------------------------------------------
        # MINIMUM ODDS
        # -------------------------------------------------

        odds_pass = (
            odd >= MINIMUM_ODDS
        )

        # -------------------------------------------------
        # EV FILTER
        # -------------------------------------------------

        ev_pass = (
            ev >= threshold
        )

        # -------------------------------------------------
        # ELIGIBILITY
        # -------------------------------------------------

        eligible = (
            odds_pass
            and ev_pass
        )

        # -------------------------------------------------
        # KELLY
        # -------------------------------------------------

        if eligible:

            kelly = quarter_kelly(
                validated_probability,
                odd,
                validated_bankroll,
            )

            stake = float(
                kelly["stake"]
            )

            quarter_kelly_value = float(
                kelly["quarter_kelly"]
            )

        else:

            stake = 0.0
            quarter_kelly_value = 0.0

        # -------------------------------------------------
        # REASON
        # -------------------------------------------------

        if eligible:

            reason = "ELIGIBLE"

        elif not odds_pass:

            reason = (
                "FILTERED: odds below "
                f"minimum {MINIMUM_ODDS:.2f}"
            )

        elif not ev_pass:

            reason = (
                "FILTERED: EV below "
                f"{threshold:.2%} threshold"
            )

        else:

            reason = "FILTERED"

        # -------------------------------------------------
        # RESULT ROW
        # -------------------------------------------------

        rows.append({
            "outcome": outcome,
            "probability": validated_probability,
            "odds": odd,
            "ev": ev,
            "eligible": eligible,
            "stake": stake,
            "quarter_kelly": quarter_kelly_value,
            "reason": reason,
        })

    # =====================================================
    # NO VALID MARKETS
    # =====================================================

    if not rows:
        raise ValueError(
            "Geçerli selection bulunamadı."
        )

    # =====================================================
    # SORT
    # =====================================================

    rows.sort(
        key=lambda x: (
            x["eligible"],
            x["ev"] if x["ev"] is not None else -1.0,
            x["probability"],
        ),
        reverse=True,
    )

    return rows
