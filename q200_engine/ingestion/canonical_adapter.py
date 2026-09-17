"""
Q200 Engine - Canonical Adapter

Q200 V3.1

CanonicalMatchData
        ↓
Canonical model fields
        ↓
TeamStats
        ↓
Q200 Model

Bu katman yalnızca validated canonical statistics verisini
Q200'ün mevcut TeamStats sözleşmesine dönüştürür.

ÖNEMLİ:
- Model hesabı yapmaz.
- Lambda hesaplamaz.
- Odds kullanmaz.
- Canonical alanların anlamını değiştirmez.
- StatsHub'taki genel AVG alanlarını home/away takım değerlerine
  tahmin ederek dönüştürmez.
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


CANONICAL_ADAPTER_VERSION = (
    "Q200-CANONICAL-ADAPTER-V1"
)


MODEL_REQUIRED_CANONICAL_FIELDS = (
    "home_gf_per_match",
    "home_ga_per_match",
    "away_gf_per_match",
    "away_ga_per_match",
)


OPTIONAL_MODEL_FIELDS = (
    "home_xg",
    "home_xga",
    "away_xga",
    "away_xg",
)


def _canonical_model_values(
    canonical: CanonicalMatchData,
) -> dict[str, Any]:
    """Canonical veriden Q200 TeamStats alanlarını seçer."""

    if not isinstance(
        canonical,
        CanonicalMatchData,
    ):
        raise TypeError(
            "canonical CanonicalMatchData olmalıdır."
        )

    values = canonical.canonical_values

    missing = [
        field
        for field in MODEL_REQUIRED_CANONICAL_FIELDS
        if field not in values
        or values[field] is None
    ]

    if missing:
        raise ValueError(
            "Canonical data Q200 TeamStats için eksik: "
            + ", ".join(missing)
        )

    mapped: dict[str, Any] = {
        "home_gf": values[
            "home_gf_per_match"
        ],
        "home_ga": values[
            "home_ga_per_match"
        ],
        "away_gf": values[
            "away_gf_per_match"
        ],
        "away_ga": values[
            "away_ga_per_match"
        ],
    }

    for field in OPTIONAL_MODEL_FIELDS:
        if (
            field in values
            and values[field] is not None
        ):
            mapped[field] = values[field]

    return mapped


def canonical_to_team_stats(
    canonical: CanonicalMatchData,
) -> TeamStats:
    """
    CanonicalMatchData → Q200 TeamStats.

    Dönüşüm:

        home_gf_per_match
            ↓
        home_gf

        home_ga_per_match
            ↓
        home_ga

        away_gf_per_match
            ↓
        away_gf

        away_ga_per_match
            ↓
        away_ga

    StatsHub'taki genel özet alanları:

        goals_avg
        xg_avg
        total_shots_avg
        possession_avg
        corners_avg

    takım tarafına tahmin edilmez.

    Bu alanlar canonical/feature katmanında
    korunmaya devam eder.
    """

    mapped = _canonical_model_values(
        canonical
    )

    return build_team_stats(
        mapped
    )


def validated_canonical_to_team_stats(
    result: ValidatedCanonicalData,
) -> TeamStats:
    """
    Validation'dan geçmiş canonical veriyi
    TeamStats'e dönüştürür.

    Validation başarısızsa Q200 TeamStats
    oluşturulmaz.
    """

    canonical = require_valid(
        result
    )

    return canonical_to_team_stats(
        canonical
    )


__all__ = [
    "CANONICAL_ADAPTER_VERSION",
    "MODEL_REQUIRED_CANONICAL_FIELDS",
    "OPTIONAL_MODEL_FIELDS",
    "canonical_to_team_stats",
    "validated_canonical_to_team_stats",
]
