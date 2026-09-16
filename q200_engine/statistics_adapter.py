"""
Q200 Engine - Statistics Adapter Layer

Q200 V3.1

Akış:

STATISTICS FILE 1
        +
STATISTICS FILE 2
        ↓
SOURCE NORMALIZATION
        ↓
SOURCE PRIORITY
        ↓
MERGED STATISTICS
        ↓
INPUT VALIDATION
        ↓
TeamStats

Kural:

Statistics File 1 > Statistics File 2

Bu katman odds kullanmaz.
Model hesabı yapmaz.
"""

from __future__ import annotations

from typing import Any, Mapping

from .input_validation import (
    ALLOWED_FIELDS,
    validate_statistics,
)
from .schema import TeamStats


# =========================================================
# SOURCE NORMALIZATION
# =========================================================

def _normalize_source(
    data: Mapping[str, Any],
    source_name: str,
) -> dict[str, Any]:
    """
    Tek statistics kaynağının field isimlerini normalize eder.

    Burada zorunlu alan kontrolü yapılmaz.

    Çünkü iki kaynağın eksik alanları daha sonra
    birleştirilerek tamamlanabilir.
    """

    if not isinstance(data, Mapping):
        raise TypeError(
            f"{source_name} mapping/dictionary olmalıdır."
        )

    normalized: dict[str, Any] = {}

    for key, value in data.items():

        if not isinstance(key, str):
            raise TypeError(
                f"{source_name} field isimleri "
                "string olmalıdır."
            )

        normalized_key = (
            key.strip()
            .lower()
        )

        if not normalized_key:
            raise ValueError(
                f"{source_name} içinde boş field "
                "adı kullanılamaz."
            )

        if normalized_key not in ALLOWED_FIELDS:
            raise ValueError(
                f"{source_name} içinde bilinmeyen "
                f"statistics alanı: {normalized_key}"
            )

        normalized[
            normalized_key
        ] = value

    return normalized


# =========================================================
# MERGE
# =========================================================

def merge_statistics_sources(
    statistics_file_1: Mapping[str, Any],
    statistics_file_2: Mapping[str, Any],
) -> dict[str, Any]:
    """
    İki statistics kaynağını Q200 öncelik kuralıyla
    birleştirir.

    Öncelik:

        File 1 > File 2

    Aynı alan iki dosyada da bulunuyorsa
    File 1 kullanılır.

    Çıktı henüz TeamStats değildir.
    """

    file_1 = _normalize_source(
        statistics_file_1,
        "statistics_file_1",
    )

    file_2 = _normalize_source(
        statistics_file_2,
        "statistics_file_2",
    )

    # Önce düşük öncelikli kaynak.
    merged = dict(file_2)

    # Sonra yüksek öncelikli kaynak.
    merged.update(file_1)

    return merged


# =========================================================
# ADAPTER
# =========================================================

def adapt_statistics_sources(
    statistics_file_1: Mapping[str, Any],
    statistics_file_2: Mapping[str, Any],
) -> TeamStats:
    """
    İki statistics kaynağını birleştirir ve
    doğrulanmış TeamStats üretir.

    Akış:

        File 1
           +
        File 2
           ↓
        Merge
           ↓
        Validation
           ↓
        TeamStats
    """

    merged = merge_statistics_sources(
        statistics_file_1,
        statistics_file_2,
    )

    return validate_statistics(
        merged
    )
