"""
Q200 Engine - Canonical Adapter

Q200 V3.1

CanonicalMatchData
        ↓
Q200 TeamStats
        ↓
Q200 Model

Bu katman yalnızca doğrulanmış canonical statistics verisini
Q200'ün mevcut TeamStats sözleşmesine dönüştürür.

ÖNEMLİ:
- Model hesabı yapmaz.
- Lambda hesaplamaz.
- Odds kullanmaz.
- Canonical alanların anlamını değiştirmez.
- Genel StatsHub AVG değerlerini home/away değerlerine tahmin ederek
  dönüştürmez.
- Q200 çekirdek lambda formülünü değiştirmez.
"""

from __future__ import annotations

from typing import Any

from ..input_validation import build_team_stats
from ..schema import TeamStats
from .models import CanonicalMatchData
from .validated_pipeline import (
    ValidatedCanonicalData,
    require_valid,
)


CANONICAL_ADAPTER_VERSION = "Q200-CANONICAL-ADAPTER-V1"

MODEL_REQUIRED_CANONICAL_FIELDS = (
    "home_gf_per_match",
    "home_ga_per_match",
    "away_gf_per_match",
    "away_ga_per_match",
)

MODEL_FIELD_MAP = {
    "home_gf_per_match": "home_gf",
    "home_ga_per_match": "home_ga",
    "away_gf_per_match": "away_gf",
    "away_ga_per_match": "away_ga",
    "home_xg": "home_xg",
    "home_xga": "home_xga",
    "away_xga": "away_xga",
    "away_xg": "away_xg",
}


def _canonical_model_values(
    canonical: CanonicalMatchData,
) -> dict[str, Any]:
    """Canonical veriden yalnızca Q200 model alanlarını seçer."""

    if not isinstance(canonical, CanonicalMatchData):
        raise TypeError(
            "canonical CanonicalMatchData olmalıdır."
        )

    values = canonical.canonical_values

    missing = [
        field
        for field in MODEL_REQUIRED_CANONICAL_FIELDS
        if field not in values or values[field] is None
    ]

    if missing:
        raise ValueError(
            "Canonical data Q200 TeamStats için eksik: "
            + ", ".join(missing)
        )

    mapped: dict[str, Any] = {}

    for canonical_field, model_field in MODEL_FIELD_MAP.items():
        if (
            canonical_field in values
            and values[canonical_field] is not None
        ):
            mapped[model_field] = values[canonical_field]

    return mapped


def canonical_to_team_stats(
    canonical: CanonicalMatchData,
) -> TeamStats:
    """
    CanonicalMatchData -> Q200 TeamStats.

    Model için zorunlu alanlar:
        home_gf_per_match -> home_gf
        home_ga_per_match -> home_ga
        away_gf_per_match -> away_gf
        away_ga_per_match -> away_ga

    Genel StatsHub alanları örneğin:
        goals_avg
        xg_avg
        total_shots_avg
        shots_on_target_avg
        possession_avg
        corners_avg

    takım tarafına tahmin edilmez ve modele sokulmaz.
    """

    mapped = _canonical_model_values(canonical)

    return build_team_stats(mapped)


def validated_canonical_to_team_stats(
    result: ValidatedCanonicalData,
) -> TeamStats:
    """
    Validation'dan geçmiş canonical veriyi TeamStats'e dönüştürür.

    Validation başarısızsa Q200 TeamStats oluşturulmaz.
    """

    canonical = require_valid(result)

    return canonical_to_team_stats(canonical)


__all__ = [
    "CANONICAL_ADAPTER_VERSION",
    "MODEL_REQUIRED_CANONICAL_FIELDS",
    "MODEL_FIELD_MAP",
    "canonical_to_team_stats",
    "validated_canonical_to_team_stats",
]
