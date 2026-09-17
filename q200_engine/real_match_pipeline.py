"""
Q200 Engine - Real Match Pipeline

Q200 V3.1

Gerçek kaynak dosyalarını tek maç akışında birleştirir:

SoccerSTATS PDF
        +
StatsHub canonical data
        ↓
Canonical Validation
        ↓
TeamStats
        ↓
Q200 Model
        ↓
MODEL LOCK
        ↓
OddsData
        ↓
Market Odds
        ↓
Q200 Analysis

ÖNEMLİ:
- Odds model oluşturulmadan önce kullanılmaz.
- Odds yalnızca MODEL LOCK sonrasında pipeline'a verilir.
- Mevcut Q200Pipeline değiştirilmez.
- Mevcut file_pipeline değiştirilmez.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .ingestion.canonical_adapter import (
    validated_canonical_to_team_stats,
)
from .ingestion.soccerstats_parser import (
    parse_soccerstats_pdf,
)
from .ingestion.validated_pipeline import (
    map_and_validate,
)
from .pipeline import Q200Pipeline
from .schema import AnalysisResult
from .odds_pdf_reader import (
    odds_data_to_market,
    parse_odds_pdf,
)


REAL_MATCH_PIPELINE_VERSION = (
    "Q200-REAL-MATCH-PIPELINE-V1"
)


def _validate_match_identity(
    statistics_match: Any,
    odds_match: Any,
) -> None:
    """
    Statistics ve Odds kaynaklarının aynı maça ait
    olduğunu doğrular.
    """

    if statistics_match is None:
        raise ValueError(
            "Statistics kaynakta maç bilgisi bulunamadı."
        )

    if odds_match is None:
        raise ValueError(
            "Odds kaynakta maç bilgisi bulunamadı."
        )

    statistics_home = (
        statistics_match.home_team
        .strip()
        .casefold()
    )

    statistics_away = (
        statistics_match.away_team
        .strip()
        .casefold()
    )

    odds_home = (
        odds_match.home_team
        .strip()
        .casefold()
    )

    odds_away = (
        odds_match.away_team
        .strip()
        .casefold()
    )

    if statistics_home != odds_home:
        raise ValueError(
            "Statistics ve Odds HOME takımları eşleşmiyor: "
            f"{statistics_match.home_team} != "
            f"{odds_match.home_team}"
        )

    if statistics_away != odds_away:
        raise ValueError(
            "Statistics ve Odds AWAY takımları eşleşmiyor: "
            f"{statistics_match.away_team} != "
            f"{odds_match.away_team}"
        )


def build_locked_model_from_soccerstats(
    statistics_pdf: str | Path,
    *,
    statshub=None,
) -> Q200Pipeline:
    """
    SoccerSTATS PDF'den modeli oluşturur.

    Bu fonksiyon Odds okumaz.

    Akış:

        SoccerSTATS
             ↓
        Canonical
             ↓
        Validation
             ↓
        TeamStats
             ↓
        Q200 MODEL
             ↓
        MODEL LOCK
    """

    soccerstats = parse_soccerstats_pdf(
        statistics_pdf
    )

    validated = map_and_validate(
        soccerstats=soccerstats,
        statshub=statshub,
    )

    stats = validated_canonical_to_team_stats(
        validated
    )

    pipeline = Q200Pipeline(
        stats
    )

    if not pipeline.model_locked:
        raise RuntimeError(
            "Q200 modeli LOCK edilmedi."
        )

    return pipeline


def run_real_match_from_pdfs(
    statistics_pdf: str | Path,
    odds_pdf: str | Path,
    *,
    market: str = "1X2",
    bankroll: float,
    uncertainty: str = "MEDIUM",
    statshub=None,
) -> AnalysisResult:
    """
    Gerçek Statistics PDF + Odds PDF ile Q200 analizi.

    Kritik sıra:

        1. Statistics PDF okunur.
        2. Canonical validation yapılır.
        3. TeamStats oluşturulur.
        4. Q200 modeli oluşturulur.
        5. MODEL LOCK gerçekleşir.
        6. Odds PDF okunur.
        7. Maç kimliği eşleştirilir.
        8. İstenen market alınır.
        9. Odds Q200Pipeline'a verilir.
        10. EV / selection / Kelly hesaplanır.

    Böylece Odds hiçbir şekilde lambda/model
    oluşturma aşamasına giremez.
    """

    if bankroll <= 0:
        raise ValueError(
            "Bankroll pozitif olmalıdır."
        )

    pipeline = build_locked_model_from_soccerstats(
        statistics_pdf,
        statshub=statshub,
    )

    soccerstats = parse_soccerstats_pdf(
        statistics_pdf
    )

    odds_data = parse_odds_pdf(
        odds_pdf
    )

    _validate_match_identity(
        soccerstats.match,
        odds_data.match,
    )

    odds = odds_data_to_market(
        odds_data,
        market,
    )

    result = pipeline.analyze_odds(
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )

    if not result.snapshot.locked:
        raise RuntimeError(
            "Analysis sonucu locked model içermiyor."
        )

    return result


__all__ = [
    "REAL_MATCH_PIPELINE_VERSION",
    "build_locked_model_from_soccerstats",
    "run_real_match_from_pdfs",
]
