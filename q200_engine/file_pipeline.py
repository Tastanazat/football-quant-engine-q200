"""
Q200 Engine - File Pipeline

Q200 V3.1

CSV / XLSX statistics dosyalarından Q200 Pipeline
analizi başlatmak için giriş katmanı.

Normal akış:

STATISTICS FILE 1
        +
STATISTICS FILE 2
        ↓
Statistics Loader
        ↓
TeamStats
        ↓
Q200Pipeline
        ↓
Odds Analysis

Data Review akışı:

DataReview 1
        +
DataReview 2
        ↓
Approval Check
        ↓
TeamStats
        ↓
Q200Pipeline
        ↓
Odds Analysis

Bu katman:
- Odds verisini model oluşturulmadan önce kullanmaz.
- Model hesaplamasını değiştirmez.
- Mevcut Q200Pipeline çekirdeğini değiştirmez.
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
    İki CSV/XLSX statistics dosyasından
    Q200 analizi çalıştırır.

    Öncelik:

        File 1 > File 2

    Model oluşturma:

        Files
          ↓
        TeamStats
          ↓
        Q200Pipeline

    Odds yalnızca Q200Pipeline'ın
    LOCK edilmiş modelinden sonra analiz edilir.
    """

    stats = load_team_stats(
        statistics_file_1=statistics_file_1,
        statistics_file_2=statistics_file_2,
        row_index_1=row_index_1,
        row_index_2=row_index_2,
    )

    pipeline = Q200Pipeline(
        stats
    )

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )


# =========================================================
# DATA REVIEW PIPELINE
# =========================================================

def run_pipeline_from_reviews(
    review_1,
    review_2,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisResult:
    """
    Onaylanmış DataReview nesnelerinden
    Q200 analizi çalıştırır.

    Akış:

        Review 1
           +
        Review 2
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

    Review'lardan biri onaysızsa
    Q200 modeli oluşturulmaz.

    Manuel olarak düzeltilmiş değerler
    doğrudan TeamStats'e aktarılır.
    """

    stats = load_team_stats_from_reviews(
        review_1,
        review_2,
    )

    pipeline = Q200Pipeline(
        stats
    )

    return pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )
