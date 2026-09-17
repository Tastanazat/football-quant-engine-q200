"""
Q200 Engine - File / Source Pipeline

Q200 V3.1

Klasik CSV/XLSX akışı:

STATISTICS FILE 1
        +
STATISTICS FILE 2
        ↓
Statistics Loader
        ↓
TeamStats
        ↓
Q200 Pipeline

Canonical source akışı:

SoccerSTATS PDF / StatsHub OCR
        ↓
Source Mapper
        ↓
CanonicalMatchData
        ↓
Validation
        ↓
Canonical Adapter
        ↓
TeamStats
        ↓
Q200 Pipeline
        ↓
Odds Analysis

Bu katman:
- Odds verisini model oluşturulmadan önce kullanmaz.
- Model hesabını değiştirmez.
- Q200Pipeline çekirdeğini değiştirmez.
- Validation başarısızsa modeli başlatmaz.
"""

from __future__ import annotations

from pathlib import Path

from .pipeline import Q200Pipeline
from .schema import AnalysisResult
from .statistics_loader import (
    load_team_stats,
    load_team_stats_from_reviews,
)


def run_pipeline_from_files(
    statistics_file_1: str | Path,
    statistics_file_2: str | Path,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
    row_index_1: int = 0,
    row_index_2: int = 0,
) -> AnalysisResult:
    """
    İki CSV/XLSX statistics dosyasından Q200 analizi çalıştırır.

    Öncelik:
        File 1 > File 2

    Model oluşturma:
        Files
          ↓
        TeamStats
          ↓
        Q200Pipeline

    Odds yalnızca Q200Pipeline'ın LOCK edilmiş modelinden sonra analiz edilir.
    """

    stats = load_team_stats(
        statistics_file_1=statistics_file_1,
        statistics_file_2=statistics_file_2,
        row_index_1=row_index_1,
        row_index_2=row_index_2,
    )

    pipeline = Q200Pipeline(stats)

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )


def run_pipeline_from_reviews(
    review_1,
    review_2,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisResult:
    """
    Onaylanmış DataReview nesnelerinden Q200 analizi çalıştırır.

    Akış:
        Review 1 + Review 2
              ↓
        APPROVAL CHECK
              ↓
        TeamStats
              ↓
        Q200 MODEL
              ↓
        MODEL LOCK
              ↓
        ODDS
              ↓
        ANALYSIS

    Bu mevcut CSV/XLSX uyumlu review akışıdır. Review değerleri
    doğrudan Q200 TeamStats alanları taşımalıdır.
    """

    stats = load_team_stats_from_reviews(
        review_1,
        review_2,
    )

    pipeline = Q200Pipeline(stats)

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )


def run_pipeline_from_sources(
    *,
    soccerstats=None,
    statshub=None,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisResult:
    """
    SoccerSTATS / StatsHub canonical kaynaklarından Q200 analizi çalıştırır.

    Akış:

        SoccerSTATS
             +
        StatsHub
             ↓
        Source Mapper
             ↓
        CanonicalMatchData
             ↓
        Validation
             ↓
        Canonical Adapter
             ↓
        TeamStats
             ↓
        Q200 MODEL
             ↓
        MODEL LOCK
             ↓
        ODDS
             ↓
        ANALYSIS

    Kaynak önceliği Source Mapper tarafından korunur:

        SoccerSTATS > StatsHub

    Ancak StatsHub'dan gelen ve SoccerSTATS'ta bulunmayan ek alanlar
    canonical veride korunur.

    Genel StatsHub AVG alanları (ör. possession_avg, corners_avg,
    total_shots_avg) home/away model alanlarına tahmin edilmez.
    """

    from .ingestion.canonical_adapter import (
        validated_canonical_to_team_stats,
    )
    from .ingestion.validated_pipeline import (
        map_and_validate,
    )

    validated = map_and_validate(
        soccerstats=soccerstats,
        statshub=statshub,
    )

    stats = validated_canonical_to_team_stats(
        validated
    )

    pipeline = Q200Pipeline(stats)

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )


__all__ = [
    "run_pipeline_from_files",
    "run_pipeline_from_reviews",
    "run_pipeline_from_sources",
]
