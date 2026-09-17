"""
Q200 Engine - PDF Pipeline

Q200 V3.1

Gerçek PDF kaynaklarını Q200 motoruna bağlayan katman.

Akış:

SoccerSTATS PDF
        ↓
SoccerStatsData
        ↓
Canonical
        ↓
Validation
        ↓
TeamStats
        ↓
Q200 Model
        ↓
MODEL LOCK
        ↓
Odds PDF
        ↓
OddsData
        ↓
Market
        ↓
Q200 Analysis

Bu katman:
- Lambda formülünü değiştirmez.
- Model hesabını değiştirmez.
- Odds'u model oluşturma aşamasında kullanmaz.
- Selection mantığını değiştirmez.
- Kelly mantığını değiştirmez.
"""

from __future__ import annotations

from pathlib import Path

from .ingestion.canonical_adapter import (
    validated_canonical_to_team_stats,
)
from .ingestion.soccerstats_parser import (
    parse_soccerstats_pdf,
)
from .ingestion.validated_pipeline import (
    map_and_validate,
)
from .odds_pdf_reader import (
    odds_data_to_market,
    parse_odds_pdf,
)
from .pipeline import Q200Pipeline
from .schema import AnalysisResult


PDF_PIPELINE_VERSION = "Q200-PDF-PIPELINE-V1"


def run_pipeline_from_pdf_sources(
    statistics_pdf: str | Path,
    odds_pdf: str | Path,
    *,
    market: str = "1X2",
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisResult:
    """
    Gerçek SoccerSTATS PDF + Odds PDF üzerinden
    Q200 analizini çalıştırır.

    Önemli sıralama:

        Statistics PDF
             ↓
        Model oluşturma
             ↓
        MODEL LOCK
             ↓
        Odds PDF
             ↓
        Odds analysis
    """

    soccerstats = parse_soccerstats_pdf(
        statistics_pdf
    )

    odds_data = parse_odds_pdf(
        odds_pdf
    )

    validated = map_and_validate(
        soccerstats=soccerstats
    )

    stats = (
        validated_canonical_to_team_stats(
            validated
        )
    )

    pipeline = Q200Pipeline(
        stats
    )

    odds = odds_data_to_market(
        odds_data,
        market
    )

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )


__all__ = [
    "PDF_PIPELINE_VERSION",
    "run_pipeline_from_pdf_sources",
]
