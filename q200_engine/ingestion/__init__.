"""
Q200 Engine - Ingestion Package

Q200 V3.1

External source ingestion layer:

    SoccerSTATS PDF
    StatsHub OCR
    Odds PDF

Bu paket external kaynaklardan gelen verilerin
canonical Q200 veri yapısına taşınmasını sağlar.

ÖNEMLİ:
Bu katman model hesabı yapmaz.
Lambda hesabı yapmaz.
Odds'u model oluştururken kullanmaz.
Selection veya Kelly hesabı yapmaz.
"""

from .models import (
    INGESTION_VERSION,
    CanonicalMatchData,
    CornerStats,
    FormStats,
    GoalStats,
    H2HStats,
    MatchInfo,
    OddsData,
    SoccerStatsData,
    SourceData,
    StatsHubData,
    TeamDistributionStats,
    TimingStats,
    model_to_dict,
)


__all__ = [
    "INGESTION_VERSION",
    "MatchInfo",
    "GoalStats",
    "CornerStats",
    "FormStats",
    "H2HStats",
    "TeamDistributionStats",
    "TimingStats",
    "SourceData",
    "SoccerStatsData",
    "StatsHubData",
    "OddsData",
    "CanonicalMatchData",
    "model_to_dict",
]
