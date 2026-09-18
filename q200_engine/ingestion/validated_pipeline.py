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

Five Source Architecture:
    1. StatsHub HOME
    2. StatsHub AWAY
    3. SoccerSTATS
    4. PPI
    5. Odds

Bu katman:
- External source'ları canonical veriye dönüştürür.
- Source priority kurallarını Source Mapper'a bırakır.
- Canonical veriyi validate eder.
- Validation sonucunu immutable bir çıktı olarak taşır.

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Odds'ı model alanlarına sokmaz.
- EV hesaplamaz.
- Selection yapmaz.
- Kelly hesaplamaz.
- Model parametrelerini değiştirmez.

ÖNEMLİ:
Odds source canonical object içerisinde taşınabilir,
ancak canonical_values içine model girdisi olarak yazılmaz.
Böylece MODEL LOCK öncesinde odds'ın model hesabını
etkilemesi engellenir.
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
from .source_mapper import map_sources


VALIDATED_INGESTION_VERSION = (
    "Q200-VALIDATED-INGESTION-V2"
)


@dataclass(frozen=True)
class ValidatedCanonicalData:
    """
    Canonical verinin validation sonucu ile birlikte
    taşınan immutable çıktısı.

    canonical:
        Source Mapper tarafından oluşturulan canonical data.

    validation:
        Canonical data validation sonucu.
    """

    canonical: CanonicalMatchData
    validation: ValidationReport

    @property
    def valid(self) -> bool:
        """
        Canonical verinin geçerli olup olmadığını döndürür.
        """

        return self.validation.valid

    @property
    def is_valid(self) -> bool:
        """
        valid property için okunabilir alias.
        """

        return self.validation.valid

    @property
    def canonical_values(
        self,
    ) -> dict[str, Any]:
        """
        Canonical model değerlerini döndürür.
        """

        return self.canonical.canonical_values

    @property
    def source_trace(
        self,
    ) -> dict[str, str]:
        """
        Her canonical alanın hangi kaynaktan geldiğini
        döndürür.
        """

        return self.canonical.source_trace

    @property
    def warnings(self) -> list[str]:
        """
        Source Mapper uyarılarını döndürür.
        """

        return self.canonical.warnings

    @property
    def match(self):
        """
        Canonical maç bilgisini döndürür.
        """

        return self.canonical.match

    @property
    def odds(self) -> OddsData | None:
        """
        Odds kaynağını döndürür.

        ÖNEMLİ:
        Odds canonical_values içinde model girdisi değildir.
        """

        return self.canonical.odds

    @property
    def source_count(self) -> int:
        """
        Mevcut external source sayısını döndürür.
        """

        sources = (
            self.canonical.statshub_home,
            self.canonical.statshub_away,
            self.canonical.soccerstats,
            self.canonical.ppi,
            self.canonical.odds,
        )

        return sum(
            source is not None
            for source in sources
        )

    @property
    def statistics_source_count(self) -> int:
        """
        Mevcut statistics source sayısını döndürür.

        Odds statistics source değildir.
        """

        sources = (
            self.canonical.statshub_home,
            self.canonical.statshub_away,
            self.canonical.soccerstats,
            self.canonical.ppi,
        )

        return sum(
            source is not None
            for source in sources
        )


def map_and_validate(
    *,
    soccerstats: SoccerStatsData | None = None,
    statshub: StatsHubData | None = None,
    statshub_home: StatsHubData | None = None,
    statshub_away: StatsHubData | None = None,
    ppi: PPIData | None = None,
    odds: OddsData | None = None,
    required_fields: tuple[str, ...] = (
        DEFAULT_REQUIRED_FIELDS
    ),
) -> ValidatedCanonicalData:
    """
    External source'ları canonical veriye dönüştürür
    ve validation uygular.

    Desteklenen kaynaklar:

        1. StatsHub HOME
        2. StatsHub AWAY
        3. SoccerSTATS
        4. PPI
        5. Odds

    Geriye dönük uyumluluk:

        statshub=

    parametresi eski tek StatsHub kullanımını
    desteklemeye devam eder.

    Yeni kullanım:

        statshub_home=
        statshub_away=
        soccerstats=
        ppi=
        odds=

    ÖNEMLİ:

    Odds canonical object içinde saklanabilir fakat
    Source Mapper tarafından canonical_values içine
    model alanı olarak yazılmaz.

    Böylece:

        Statistics
             ↓
        Canonical
             ↓
        Validation

    aşamasında Odds model oluşturmayı etkileyemez.
    """

    if not isinstance(
        required_fields,
        tuple,
    ):
        raise TypeError(
            "required_fields tuple olmalıdır."
        )

    if (
        statshub is not None
        and (
            statshub_home is not None
            or statshub_away is not None
        )
    ):
        raise ValueError(
            "statshub ile statshub_home/"
            "statshub_away aynı anda "
            "kullanılamaz."
        )

    # En az bir STATISTICS source gereklidir.
    #
    # Odds tek başına bir statistics source değildir.
    statistics_sources = (
        soccerstats,
        statshub,
        statshub_home,
        statshub_away,
        ppi,
    )

    if all(
        source is None
        for source in statistics_sources
    ):
        raise ValueError(
            "En az bir statistics source "
            "verilmelidir."
        )

    canonical = map_sources(
        soccerstats=soccerstats,
        statshub=statshub,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        ppi=ppi,
        odds=odds,
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

    Odds burada canonical_values içine
    eklenmez.

    Odds gerekiyorsa:
        result.odds

    üzerinden ayrıca alınabilir.
    """

    if not isinstance(
        result,
        ValidatedCanonicalData,
    ):
        raise TypeError(
            "result ValidatedCanonicalData "
            "olmalıdır."
        )

    odds_payload: dict[str, Any] | None = None

    if result.odds is not None:
        odds_payload = {
            "match": {
                "home_team": (
                    result.odds.match.home_team
                    if result.odds.match is not None
                    else None
                ),
                "away_team": (
                    result.odds.match.away_team
                    if result.odds.match is not None
                    else None
                ),
                "date": (
                    result.odds.match.date
                    if result.odds.match is not None
                    else None
                ),
                "time": (
                    result.odds.match.time
                    if result.odds.match is not None
                    else None
                ),
                "competition": (
                    result.odds.match.competition
                    if result.odds.match is not None
                    else None
                ),
            },
            "markets": {
                market: dict(values)
                for market, values
                in result.odds.markets.items()
            },
        }

    return {
        "pipeline_version": (
            VALIDATED_INGESTION_VERSION
        ),
        "valid": result.valid,
        "source_count": result.source_count,
        "statistics_source_count": (
            result.statistics_source_count
        ),
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
        "odds": odds_payload,
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
