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

Desteklenen kaynaklar:

1. StatsHub HOME
2. StatsHub AWAY
3. SoccerSTATS
4. PPI
5. Odds

Bu katman:
- Kaynakları canonical yapıya dönüştürür.
- Canonical veriyi validate eder.
- Validation sonucunu taşır.
- 5 kaynaklı akışı destekler.

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Odds'u model oluşturma aşamasına sokmaz.
- Selection yapmaz.
- Kelly hesaplamaz.
- Model parametrelerini değiştirmez.

Backward compatibility:
- Eski map_and_validate() API korunur.
- Yeni map_and_validate_five_sources() eklenir.
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
    OddsData,
    PPIData,
    SoccerStatsData,
    StatsHubData,
)
from .source_mapper import (
    map_five_sources,
    map_sources,
)


VALIDATED_INGESTION_VERSION = (
    "Q200-VALIDATED-INGESTION-V2"
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


def _validate_required_fields(
    required_fields: tuple[str, ...],
) -> None:
    """
    required_fields sözleşmesini kontrol eder.
    """

    if not isinstance(
        required_fields,
        tuple,
    ):
        raise TypeError(
            "required_fields tuple olmalıdır."
        )

    if not all(
        isinstance(field, str)
        for field in required_fields
    ):
        raise TypeError(
            "required_fields içindeki alan adları "
            "string olmalıdır."
        )


def _validate_canonical(
    canonical: CanonicalMatchData,
    required_fields: tuple[str, ...],
) -> ValidatedCanonicalData:
    """
    CanonicalMatchData üzerinde validation çalıştırır.
    """

    validation = validate_canonical_data(
        canonical,
        required_fields=required_fields,
    )

    return ValidatedCanonicalData(
        canonical=canonical,
        validation=validation,
    )


def map_and_validate(
    *,
    soccerstats: SoccerStatsData | None = None,
    statshub: StatsHubData | None = None,
    required_fields: tuple[str, ...] = (
        DEFAULT_REQUIRED_FIELDS
    ),
) -> ValidatedCanonicalData:
    """
    Eski tek StatsHub API'si için backward-compatible
    validation pipeline.

    Akış:

        SoccerSTATS
             +
        StatsHub
             ↓
        map_sources()
             ↓
        CanonicalMatchData
             ↓
        Validation

    Bu fonksiyon korunmuştur.
    """

    if (
        soccerstats is None
        and statshub is None
    ):
        raise ValueError(
            "En az bir statistics source "
            "verilmelidir."
        )

    _validate_required_fields(
        required_fields
    )

    canonical = map_sources(
        soccerstats=soccerstats,
        statshub=statshub,
    )

    return _validate_canonical(
        canonical,
        required_fields,
    )


def map_and_validate_five_sources(
    *,
    soccerstats: SoccerStatsData | None = None,
    statshub_home: StatsHubData | None = None,
    statshub_away: StatsHubData | None = None,
    ppi: PPIData | None = None,
    odds: OddsData | None = None,
    required_fields: tuple[str, ...] = (
        DEFAULT_REQUIRED_FIELDS
    ),
) -> ValidatedCanonicalData:
    """
    Q200 V3.1 beş kaynaklı validation pipeline.

    Kaynaklar:

        1. StatsHub HOME
        2. StatsHub AWAY
        3. SoccerSTATS
        4. PPI
        5. Odds

    Akış:

        Five Sources
             ↓
        map_five_sources()
             ↓
        CanonicalMatchData
             ↓
        Validation
             ↓
        ValidatedCanonicalData

    ÖNEMLİ:

    Odds CanonicalMatchData.odds içinde tutulur.

    Odds değerleri canonical_values içine yazılmaz
    ve model oluşturma aşamasında kullanılmaz.

    PPI context olarak korunur.

    Validation başarısızsa canonical veri silinmez;
    result.valid False olur ve require_valid()
    sonraki model aşamasını engeller.
    """

    if all(
        source is None
        for source in (
            soccerstats,
            statshub_home,
            statshub_away,
            ppi,
            odds,
        )
    ):
        raise ValueError(
            "En az bir source verilmelidir."
        )

    _validate_required_fields(
        required_fields
    )

    canonical = map_five_sources(
        soccerstats=soccerstats,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        ppi=ppi,
        odds=odds,
    )

    return _validate_canonical(
        canonical,
        required_fields,
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
    "map_and_validate_five_sources",
    "require_valid",
    "validated_pipeline_to_dict",
]
