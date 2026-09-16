"""
Q200 Engine - Odds Layer

Q200 V3.1
"""

from __future__ import annotations

from math import isfinite


# =========================================================
# IMPLIED PROBABILITIES
# =========================================================

def implied_probabilities(
    odds: dict[str, float],
) -> dict[str, float]:

    if not isinstance(odds, dict):
        raise TypeError(
            "Odds dictionary olmalıdır."
        )

    if not odds:
        raise ValueError(
            "Odds boş olamaz."
        )

    for outcome, odd in odds.items():

        try:
            odd = float(odd)
        except (TypeError, ValueError):
            raise ValueError(
                f"{outcome} oranı geçersiz."
            )

        if not isfinite(odd):
            raise ValueError(
                f"{outcome} oranı finite olmalıdır."
            )

        if odd <= 1.0:
            raise ValueError(
                f"{outcome} oranı 1.00'dan büyük olmalıdır."
            )

    raw = {
        outcome: 1.0 / float(odd)
        for outcome, odd in odds.items()
    }

    total = sum(raw.values())

    if total <= 0 or not isfinite(total):
        raise ValueError(
            "Implied probability toplamı geçersiz."
        )

    return {
        outcome: probability / total
        for outcome, probability in raw.items()
    }


# =========================================================
# REMOVE VIG / NO-VIG
# =========================================================

def remove_vig(
    probabilities: dict[str, float],
) -> dict[str, float]:
    """
    Bookmaker marjını (vig/overround) kaldırır.

    Girdi:
        Ham implied probability değerleri.

    Çıktı:
        Toplamı tam olarak 1.0 olan normalize edilmiş
        no-vig probability değerleri.

    Örnek:

        {
            "HOME": 0.50,
            "DRAW": 0.30,
            "AWAY": 0.25
        }

    toplam = 1.05

    sonuç:

        {
            "HOME": 0.47619...,
            "DRAW": 0.28571...,
            "AWAY": 0.23809...
        }

    ÖNEMLİ:

    Bu fonksiyon model olasılıklarını değiştirmez.
    Sadece odds tarafından oluşturulan implied
    probability dağılımını normalize eder.
    """

    if not isinstance(probabilities, dict):
        raise TypeError(
            "Probabilities dictionary olmalıdır."
        )

    if not probabilities:
        raise ValueError(
            "Probabilities boş olamaz."
        )

    validated = {}

    for outcome, probability in probabilities.items():

        try:
            value = float(probability)
        except (TypeError, ValueError):
            raise ValueError(
                f"{outcome} probability değeri geçersiz."
            )

        if not isfinite(value):
            raise ValueError(
                f"{outcome} probability finite olmalıdır."
            )

        if value < 0.0 or value > 1.0:
            raise ValueError(
                f"{outcome} probability 0 ile 1 arasında olmalıdır."
            )

        validated[outcome] = value

    total = sum(validated.values())

    if total <= 0 or not isfinite(total):
        raise ValueError(
            "Probability toplamı sıfırdan büyük olmalıdır."
        )

    return {
        outcome: probability / total
        for outcome, probability in validated.items()
    }


# =========================================================
# FAIR ODDS
# =========================================================

def fair_odds(
    probabilities: dict[str, float],
) -> dict[str, float]:

    if not isinstance(probabilities, dict):
        raise TypeError(
            "Probabilities dictionary olmalıdır."
        )

    if not probabilities:
        raise ValueError(
            "Probabilities boş olamaz."
        )

    result = {}

    for outcome, probability in probabilities.items():

        try:
            probability = float(probability)
        except (TypeError, ValueError):
            raise ValueError(
                f"{outcome} probability değeri geçersiz."
            )

        if not isfinite(probability):
            raise ValueError(
                f"{outcome} probability finite olmalıdır."
            )

        if probability < 0.0 or probability > 1.0:
            raise ValueError(
                f"{outcome} probability 0 ile 1 arasında olmalıdır."
            )

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

    try:
        probability = float(probability)
        odds = float(odds)
    except (TypeError, ValueError):
        raise ValueError(
            "Probability ve odds numeric olmalıdır."
        )

    if not isfinite(probability):
        raise ValueError(
            "Probability finite olmalıdır."
        )

    if not isfinite(odds):
        raise ValueError(
            "Odds finite olmalıdır."
        )

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
