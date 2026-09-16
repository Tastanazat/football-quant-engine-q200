"""
Q200 Selection Engine

Model olasılıkları ve value/EV sonuçlarına göre seçim filtresi.
Oranlar model oluşturma aşamasını etkilemez.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


MIN_ODDS = 1.50

EV_THRESHOLDS = {
    "low": 0.05,
    "medium": 0.08,
    "high": 0.12,
    "very_high": float("inf"),
}


def _get_value(data: Any, *keys: str, default=None):
    """Dict veya object içerisinden ilk bulunan değeri alır."""
    if isinstance(data, dict):
        for key in keys:
            if key in data:
                return data[key]

    for key in keys:
        if hasattr(data, key):
            return getattr(data, key)

    return default


def uncertainty_threshold(uncertainty: str) -> float:
    """
    Belirsizlik seviyesine göre minimum EV eşiğini döndürür.
    """
    level = str(uncertainty).lower().strip()

    if level in {"very_high", "very high", "çok yüksek", "cok yuksek"}:
        return float("inf")

    return EV_THRESHOLDS.get(level, EV_THRESHOLDS["high"])


def is_eligible(
    odds: float,
    ev: float,
    uncertainty: str = "high",
    min_odds: float = MIN_ODDS,
) -> bool:
    """
    Bir seçimin Q200 kurallarına uygun olup olmadığını kontrol eder.
    """

    try:
        odds = float(odds)
        ev = float(ev)
    except (TypeError, ValueError):
        return False

    if odds < min_odds:
        return False

    threshold = uncertainty_threshold(uncertainty)

    if threshold == float("inf"):
        return False

    return ev >= threshold


def select(
    selections: Iterable[Any],
    min_odds: float = MIN_ODDS,
) -> List[Any]:
    """
    Uygun seçimleri filtreler.

    Beklenen alanlar:
        odds
        ev
        uncertainty
    """

    result = []

    for item in selections:
        odds = _get_value(item, "odds", "odd", "price")
        ev = _get_value(item, "ev", "expected_value", "EV")
        uncertainty = _get_value(
            item,
            "uncertainty",
            "uncertainty_level",
            "risk_level",
            default="high",
        )

        if odds is None or ev is None:
            continue

        if is_eligible(
            odds=odds,
            ev=ev,
            uncertainty=uncertainty,
            min_odds=min_odds,
        ):
            result.append(item)

    return result


def select_best(
    selections: Iterable[Any],
    min_odds: float = MIN_ODDS,
) -> Optional[Any]:
    """
    Uygun seçimler içerisinden en yüksek EV değerine sahip olanı döndürür.

    Bu fonksiyon yalnızca teknik filtreleme yapar.
    """

    eligible = select(selections, min_odds=min_odds)

    if not eligible:
        return None

    return max(
        eligible,
        key=lambda item: float(
            _get_value(
                item,
                "ev",
                "expected_value",
                "EV",
                default=0.0,
            )
        ),
    )


def filter_selections(
    selections: Iterable[Any],
    min_odds: float = MIN_ODDS,
) -> List[Any]:
    """
    select() için geriye dönük uyumluluk alias'ı.
    """
    return select(selections, min_odds=min_odds)


__all__ = [
    "MIN_ODDS",
    "EV_THRESHOLDS",
    "uncertainty_threshold",
    "is_eligible",
    "select",
    "select_best",
    "filter_selections",
]
