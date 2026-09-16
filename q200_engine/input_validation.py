"""
Q200 Engine - Input Validation Layer

Q200 V3.1

Görev:

Dışarıdan gelen istatistik verisini
Q200 TeamStats modeline dönüştürmek.

Akış:

RAW STATISTICS
      ↓
INPUT VALIDATION
      ↓
NORMALIZATION
      ↓
TeamStats
      ↓
Q200 MODEL

Bu katman model olasılıklarını veya oranları değiştirmez.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

from .schema import TeamStats


# =========================================================
# REQUIRED / OPTIONAL FIELDS
# =========================================================

REQUIRED_FIELDS = {
    "home_gf",
    "home_ga",
    "away_gf",
}

OPTIONAL_FIELDS = {
    "away_ga",
    "home_xg",
    "home_xga",
    "away_xga",
    "away_xg",
}

ALLOWED_FIELDS = (
    REQUIRED_FIELDS
    | OPTIONAL_FIELDS
)


# =========================================================
# NUMBER VALIDATION
# =========================================================

def _validate_number(
    value: Any,
    field_name: str,
) -> float:
    """
    Değeri güvenli float değerine dönüştürür.

    Kabul edilir:

        1
        1.5
        "1.5"

    Kabul edilmez:

        None
        True / False
        ""
        "abc"
        NaN
        Infinity
        negatif değerler
    """

    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} boolean olamaz."
        )

    if value is None:
        raise ValueError(
            f"{field_name} boş olamaz."
        )

    try:
        result = float(value)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} sayısal olmalıdır."
        ) from exc

    if not isfinite(result):
        raise ValueError(
            f"{field_name} finite bir sayı olmalıdır."
        )

    if result < 0:
        raise ValueError(
            f"{field_name} negatif olamaz."
        )

    return result


# =========================================================
# OPTIONAL NUMBER VALIDATION
# =========================================================

def _validate_optional_number(
    value: Any,
    field_name: str,
) -> float | None:
    """
    Opsiyonel istatistik alanını doğrular.

    None ise None olarak kalır.
    """

    if value is None:
        return None

    return _validate_number(
        value,
        field_name,
    )


# =========================================================
# INPUT NORMALIZATION
# =========================================================

def normalize_statistics(
    data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Ham istatistik sözlüğünü normalize eder.

    Alan adları küçük harfe çevrilir.

    Örneğin:

        HOME_GF
        Home_GF
        home_gf

    → home_gf

    Değerler henüz TeamStats'e dönüştürülmez.
    """

    if not isinstance(data, Mapping):
        raise TypeError(
            "Statistics input mapping/dictionary olmalıdır."
        )

    normalized: dict[str, Any] = {}

    for key, value in data.items():

        if not isinstance(key, str):
            raise TypeError(
                "Statistics field isimleri string olmalıdır."
            )

        normalized_key = (
            key.strip()
            .lower()
        )

        if not normalized_key:
            raise ValueError(
                "Boş field adı kullanılamaz."
            )

        normalized[
            normalized_key
        ] = value

    # -----------------------------------------------------
    # UNKNOWN FIELDS
    # -----------------------------------------------------

    unknown_fields = (
        set(normalized)
        - ALLOWED_FIELDS
    )

    if unknown_fields:

        unknown = ", ".join(
            sorted(unknown_fields)
        )

        raise ValueError(
            f"Bilinmeyen statistics alanı: {unknown}"
        )

    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------

    missing_fields = (
        REQUIRED_FIELDS
        - set(normalized)
    )

    if missing_fields:

        missing = ", ".join(
            sorted(missing_fields)
        )

        raise ValueError(
            f"Eksik zorunlu statistics alanı: {missing}"
        )

    return normalized


# =========================================================
# BUILD TEAM STATS
# =========================================================

def build_team_stats(
    data: Mapping[str, Any],
) -> TeamStats:
    """
    Ham statistics verisini TeamStats'e dönüştürür.

    Bu fonksiyon Q200 modelinin beklediği veri yapısını
    oluşturur.

    Model hesabı yapmaz.
    Odds kullanmaz.
    """

    normalized = normalize_statistics(
        data
    )

    # -----------------------------------------------------
    # REQUIRED
    # -----------------------------------------------------

    home_gf = _validate_number(
        normalized["home_gf"],
        "home_gf",
    )

    home_ga = _validate_number(
        normalized["home_ga"],
        "home_ga",
    )

    away_gf = _validate_number(
        normalized["away_gf"],
        "away_gf",
    )

    # -----------------------------------------------------
    # OPTIONAL
    # -----------------------------------------------------

    away_ga = (
        _validate_number(
            normalized["away_ga"],
            "away_ga",
        )
        if "away_ga" in normalized
        else 0.0
    )

    home_xg = _validate_optional_number(
        normalized.get("home_xg"),
        "home_xg",
    )

    home_xga = _validate_optional_number(
        normalized.get("home_xga"),
        "home_xga",
    )

    away_xga = _validate_optional_number(
        normalized.get("away_xga"),
        "away_xga",
    )

    away_xg = _validate_optional_number(
        normalized.get("away_xg"),
        "away_xg",
    )

    # -----------------------------------------------------
    # TEAM STATS
    # -----------------------------------------------------

    return TeamStats(
        home_gf=home_gf,
        home_ga=home_ga,
        away_gf=away_gf,
        away_ga=away_ga,
        home_xg=home_xg,
        home_xga=home_xga,
        away_xga=away_xga,
        away_xg=away_xg,
    )


# =========================================================
# VALIDATE TEAM STATS
# =========================================================

def validate_team_stats(
    stats: TeamStats,
) -> TeamStats:
    """
    Hazır TeamStats nesnesini tekrar doğrular.

    Başarılıysa aynı nesneyi döndürür.
    """

    if not isinstance(
        stats,
        TeamStats,
    ):
        raise TypeError(
            "stats TeamStats nesnesi olmalıdır."
        )

    # -----------------------------------------------------
    # REQUIRED
    # -----------------------------------------------------

    _validate_number(
        stats.home_gf,
        "home_gf",
    )

    _validate_number(
        stats.home_ga,
        "home_ga",
    )

    _validate_number(
        stats.away_gf,
        "away_gf",
    )

    # -----------------------------------------------------
    # OPTIONAL / DEFAULT
    # -----------------------------------------------------

    _validate_number(
        stats.away_ga,
        "away_ga",
    )

    _validate_optional_number(
        stats.home_xg,
        "home_xg",
    )

    _validate_optional_number(
        stats.home_xga,
        "home_xga",
    )

    _validate_optional_number(
        stats.away_xga,
        "away_xga",
    )

    _validate_optional_number(
        stats.away_xg,
        "away_xg",
    )

    return stats


# =========================================================
# PUBLIC CONVENIENCE FUNCTION
# =========================================================

def validate_statistics(
    data: Mapping[str, Any],
) -> TeamStats:
    """
    Tek çağrıyla:

        RAW DATA
          ↓
        NORMALIZE
          ↓
        VALIDATE
          ↓
        TeamStats

    üretir.
    """

    stats = build_team_stats(
        data
    )

    return validate_team_stats(
        stats
    )
