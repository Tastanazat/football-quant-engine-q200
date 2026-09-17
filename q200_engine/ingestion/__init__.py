"""
Q200 Engine - Ingestion Package

Q200 V3.1

External source ingestion layer:

    SoccerSTATS PDF
    StatsHub OCR
    Odds PDF
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

from .soccerstats_parser import (
    SOCCERSTATS_PARSER_VERSION,
    extract_pdf_text,
    parse_soccerstats_text,
    parse_soccerstats_pdf,
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
    "SOCCERSTATS_PARSER_VERSION",
    "extract_pdf_text",
    "parse_soccerstats_text",
    "parse_soccerstats_pdf",
]
