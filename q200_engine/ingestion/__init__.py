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

from .source_mapper import (
    SOURCE_MAPPER_VERSION,
    map_soccerstats,
    map_sources,
)

from .data_validator import (
    DATA_VALIDATOR_VERSION,
    DEFAULT_REQUIRED_FIELDS,
    ValidationIssue,
    ValidationReport,
    validate_canonical_values,
    validate_canonical_data,
    validation_to_dict,
)

from .validated_pipeline import (
    VALIDATED_INGESTION_VERSION,
    ValidatedCanonicalData,
    map_and_validate,
    require_valid,
    validated_pipeline_to_dict,
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
    "SOURCE_MAPPER_VERSION",
    "map_soccerstats",
    "map_sources",
    "DATA_VALIDATOR_VERSION",
    "DEFAULT_REQUIRED_FIELDS",
    "ValidationIssue",
    "ValidationReport",
    "validate_canonical_values",
    "validate_canonical_data",
    "validation_to_dict",
    "VALIDATED_INGESTION_VERSION",
    "ValidatedCanonicalData",
    "map_and_validate",
    "require_valid",
    "validated_pipeline_to_dict",
]
