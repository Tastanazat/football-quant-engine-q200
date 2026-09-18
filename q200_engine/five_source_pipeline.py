"""
Q200 Engine - Five Source Pipeline

Q200 V3.1

Five sources:
    1. StatsHub HOME
    2. StatsHub AWAY
    3. SoccerSTATS
    4. PPI
    5. Odds

Akış:

FiveSourceMatchInput
        ↓
Five Source Mapper
        ↓
CanonicalMatchData
        ↓
Validation
        ↓
TeamStats
        ↓
Q200 Model
        ↓
MODEL LOCK
        ↓
Odds
        ↓
Q200 Analysis

Bu katman mevcut Q200 çekirdeğini değiştirmez.
"""

from __future__ import annotations

from .ingestion.canonical_adapter import (
    canonical_to_team_stats,
)
from .ingestion.data_validator import (
    DEFAULT_REQUIRED_FIELDS,
    validate_canonical_data,
)
from .ingestion.models import (
    FiveSourceMatchInput,
)
from .ingestion.source_mapper import (
    map_five_sources,
)
from .pipeline import Q200Pipeline
from .schema import AnalysisResult
from .odds_pdf_reader import (
    odds_data_to_market,
)


FIVE_SOURCE_PIPELINE_VERSION = (
    "Q200-FIVE-SOURCE-PIPELINE-V1"
)


def _validate_input(
    data: FiveSourceMatchInput,
) -> None:
    """
    FiveSourceMatchInput sözleşmesini doğrular.
    """

    if not isinstance(
        data,
        FiveSourceMatchInput,
    ):
        raise TypeError(
            "data FiveSourceMatchInput olmalıdır."
        )

    if data.statistics_source_count == 0:
        raise ValueError(
            "En az bir statistics source "
            "verilmelidir."
        )


def build_locked_model_from_five_sources(
    data: FiveSourceMatchInput,
    *,
    required_fields: tuple[str, ...] = (
        DEFAULT_REQUIRED_FIELDS
    ),
) -> Q200Pipeline:
    """
    FiveSourceMatchInput üzerinden Q200 modelini oluşturur.

    Odds model oluşturma aşamasında kullanılmaz.

    Model oluşturulduktan sonra Q200Pipeline
    tarafından LOCK edilir.
    """

    _validate_input(data)

    if not isinstance(
        required_fields,
        tuple,
    ):
        raise TypeError(
            "required_fields tuple olmalıdır."
        )

    canonical = map_five_sources(
        soccerstats=data.soccerstats,
        statshub_home=data.statshub_home,
        statshub_away=data.statshub_away,
        ppi=data.ppi,
        odds=data.odds,
    )

    validation = validate_canonical_data(
        canonical,
        required_fields=required_fields,
    )

    if not validation.valid:

        missing = list(
            validation.missing_fields
        )

        issue_codes = [
            issue.code
            for issue in validation.issues
        ]

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
            "Five-source canonical validation "
            "başarısız: "
            + detail_text
        )

    stats = canonical_to_team_stats(
        canonical
    )

    pipeline = Q200Pipeline(
        stats
    )

    if not pipeline.model_locked:
        raise RuntimeError(
            "Q200 modeli LOCK edilmeden "
            "pipeline tamamlanamaz."
        )

    return pipeline


def run_five_source_analysis(
    data: FiveSourceMatchInput,
    *,
    market: str = "1X2",
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisResult:
    """
    Beş kaynaklı tam Q200 analizini çalıştırır.

    Kritik sıra:

        Statistics sources
            ↓
        Model
            ↓
        MODEL LOCK
            ↓
        Odds
            ↓
        Analysis

    Odds yoksa tam analiz çalıştırılmaz.
    """

    _validate_input(data)

    if data.odds is None:
        raise ValueError(
            "Tam five-source analysis için "
            "OddsData gereklidir."
        )

    pipeline = (
        build_locked_model_from_five_sources(
            data
        )
    )

    odds = odds_data_to_market(
        data.odds,
        market,
    )

    result = pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )

    if not result.snapshot.locked:
        raise RuntimeError(
            "Analysis sonucu locked model "
            "içermiyor."
        )

    return result


__all__ = [
    "FIVE_SOURCE_PIPELINE_VERSION",
    "build_locked_model_from_five_sources",
    "run_five_source_analysis",
]
