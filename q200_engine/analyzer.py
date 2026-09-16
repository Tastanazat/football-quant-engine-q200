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
        ↓
OPTIONAL HISTORY SAVE
"""

from __future__ import annotations

from pathlib import Path

from .file_pipeline import run_pipeline_from_files
from .history import AnalysisHistory
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
    history_path: str | Path | None = None,
    match_id: str | None = None,
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
        ↓
        Optional History Save

    history_path ve match_id birlikte verilirse analiz sonucu
    otomatik olarak SQLite History'ye kaydedilir.

    İkisinden yalnızca biri verilirse ValueError oluşur.
    """

    if (
        history_path is None
        and match_id is not None
    ):
        raise ValueError(
            "match_id verildiyse history_path da verilmelidir."
        )

    if (
        history_path is not None
        and match_id is None
    ):
        raise ValueError(
            "history_path verildiyse match_id de verilmelidir."
        )

    odds = read_odds_dict(
        odds_file
    )

    result = run_pipeline_from_files(
        statistics_file_1=statistics_file_1,
        statistics_file_2=statistics_file_2,
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
        row_index_1=row_index_1,
        row_index_2=row_index_2,
    )

    if (
        history_path is not None
        and match_id is not None
    ):
        history = AnalysisHistory(
            history_path
        )

        history.save(
            result,
            match_id,
        )

    return result
