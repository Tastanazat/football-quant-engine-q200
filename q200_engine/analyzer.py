"""
Q200 Engine - File Analyzer

Q200 V3.1

Üç dosyadan tam Q200 analiz girişi:

STATISTICS FILE 1
        +
STATISTICS FILE 2
        +
ODDS FILE
        ↓
Q200 ANALYSIS
"""

from __future__ import annotations

from pathlib import Path

from .file_pipeline import run_pipeline_from_files
from .odds_reader import read_odds_dict
from .schema import AnalysisResult


def run_q200_from_files(
    statistics_file_1: str | Path,
    statistics_file_2: str | Path,
    odds_file: str | Path,
    bankroll: float,
    uncertainty: str = "MEDIUM",
    row_index_1: int = 0,
    row_index_2: int = 0,
) -> AnalysisResult:
    """
    Statistics File 1 + Statistics File 2 + Odds File
    üzerinden tam Q200 V3.1 analizini çalıştırır.

    Sıra:

        Statistics 1
        Statistics 2
        ↓
        TeamStats
        ↓
        Q200 Model
        ↓
        Model LOCK
        ↓
        Odds Reader
        ↓
        Odds Analysis

    Odds modeli oluşturmaz ve model LOCK edildikten sonra
    yalnızca analiz aşamasında kullanılır.
    """

    odds = read_odds_dict(
        odds_file
    )

    return run_pipeline_from_files(
        statistics_file_1=statistics_file_1,
        statistics_file_2=statistics_file_2,
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
        row_index_1=row_index_1,
        row_index_2=row_index_2,
    )
