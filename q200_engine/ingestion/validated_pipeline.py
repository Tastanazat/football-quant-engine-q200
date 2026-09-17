"""
Q200 Engine - Validated Ingestion Pipeline

Q200 V3.1

External Sources
        ↓
Source Mapper
        ↓
CanonicalMatchData
        ↓
Validation
        ↓
Validated Canonical Data

Bu katman:
- SoccerSTATS ve StatsHub verilerini birleştirir.
- Mevcut Source Mapper önceliklerini korur.
- Canonical veriyi validate eder.
- Validation sonucunu taşıyan tek bir çıktı üretir.

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Odds kullanmaz.
- Selection yapmaz.
- Kelly hesaplamaz.
- Model parametrelerini değiştirmez.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_validator import (
    DEFAULT_REQUIRED_FIELDS,
    ValidationReport,
    validate_canonical_data,
)
from .models import (
    CanonicalMatchData,
    SoccerStatsData,
    StatsHubData,
)
from .source_mapper import map_sources


VALIDATED_INGESTION_VERSION = (
    "Q200-VALIDATED-INGESTION-V1"
)


@dataclass(frozen=True)
class ValidatedCanonicalData:
    """
    Canonical verinin validation sonucu ile birlikte
    taşınan immutable çıktısı.
    """

    canonical: CanonicalMatchData
    validation: ValidationReport

    @property
    def valid(self) -> bool:
        return self.validation.valid

    @property
    def is_valid(self) -> bool:
        return self.validation.valid

    @property
    def canonical_values(
        self,
    ) -> dict[str, Any]:
        return self.canonical.canonical_values

    @property
    def source_trace(
        self,
    ) -> dict[str, str]:
        return self.canonical.source_trace

    @property
    def warnings(self) -> list[str]:
        return self.canonical.warnings


def map_and_validate(
    *,
    soccerstats: SoccerStatsData | None = None,
    statshub: StatsHubData | None = None,
    required_fields: tuple[str, ...] = (
        DEFAULT_REQUIRED_FIELDS
    ),
) -> ValidatedCanonicalData:
    """
    External source'ları canonical veriye dönüştürür
    ve validation uygular.

    ÖNEMLİ:

    Validation başarısız olsa bile ham canonical veri
    silinmez.

    Sonuç:
        result.canonical
        result.validation

    üzerinden hem veri hem de validation problemi
    birlikte görülebilir.
    """

    if (
        soccerstats is None
        and statshub is None
    ):
        raise ValueError(
            "En az bir statistics source "
            "verilmelidir."
        )

    if not isinstance(
        required_fields,
        tuple,
    ):
        raise TypeError(
            "required_fields tuple olmalıdır."
        )

    canonical = map_sources(
        soccerstats=soccerstats,
        statshub=statshub,
    )

    validation = validate_canonical_data(
        canonical,
        required_fields=required_fields,
    )

    return ValidatedCanonicalData(
        canonical=canonical,
        validation=validation,
    )


def require_valid(
    result: ValidatedCanonicalData,
) -> CanonicalMatchData:
    """
    Validation'dan geçmeyen canonical verinin
    sonraki aşamaya aktarılmasını engeller.

    Geçerli veri:
        CanonicalMatchData

    Geçersiz veri:
        ValueError
    """

    if not isinstance(
        result,
        ValidatedCanonicalData,
    ):
        raise TypeError(
            "result ValidatedCanonicalData "
            "olmalıdır."
        )

    if not result.valid:
        issue_codes = [
            issue.code
            for issue in result.validation.issues
        ]

        missing = list(
            result.validation.missing_fields
        )

        details: list[str] = []

        if missing:
            details.append(
                "missing="
                + ",".join(missing)
            )

        if issue_codes:
            details.append(
                "issues="
                + ",".join(issue_codes)
            )

        detail_text = (
            "; ".join(details)
            if details
            else "validation başarısız"
        )

        raise ValueError(
            "Canonical data validation "
            f"başarısız: {detail_text}"
        )

    return result.canonical


def validated_pipeline_to_dict(
    result: ValidatedCanonicalData,
) -> dict[str, Any]:
    """
    Validation pipeline sonucunu JSON uyumlu
    dict'e dönüştürür.
    """

    if not isinstance(
        result,
        ValidatedCanonicalData,
    ):
        raise TypeError(
            "result ValidatedCanonicalData "
            "olmalıdır."
        )

    return {
        "pipeline_version": (
            VALIDATED_INGESTION_VERSION
        ),
        "valid": result.valid,
        "canonical": {
            "match": {
                "home_team": (
                    result.canonical.match.home_team
                ),
                "away_team": (
                    result.canonical.match.away_team
                ),
                "date": (
                    result.canonical.match.date
                ),
                "time": (
                    result.canonical.match.time
                ),
                "competition": (
                    result.canonical.match.competition
                ),
                "source": (
                    result.canonical.match.source
                ),
            },
            "canonical_values": dict(
                result.canonical.canonical_values
            ),
            "source_trace": dict(
                result.canonical.source_trace
            ),
            "warnings": list(
                result.canonical.warnings
            ),
        },
        "validation": {
            "validator_version": (
                result.validation.validator_version
            ),
            "valid": (
                result.validation.valid
            ),
            "checked_fields": (
                result.validation.checked_fields
            ),
            "valid_fields": (
                result.validation.valid_fields
            ),
            "missing_fields": list(
                result.validation.missing_fields
            ),
            "issues": [
                {
                    "field": issue.field,
                    "value": issue.value,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in result.validation.issues
            ],
            "warnings": list(
                result.validation.warnings
            ),
        },
    }


__all__ = [
    "VALIDATED_INGESTION_VERSION",
    "ValidatedCanonicalData",
    "map_and_validate",
    "require_valid",
    "validated_pipeline_to_dict",
]
