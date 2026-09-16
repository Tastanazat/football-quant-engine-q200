"""
Q200 Engine

Q200 V3.1
"""

from .schema import (
    TeamStats,
    ModelSnapshot,
    OddsInput,
    AnalysisResult,
)

from .model import (
    calculate_lambdas,
    build_model,
)

from .poisson_model import (
    poisson_pmf,
    poisson_score_matrix,
    poisson_match_probabilities,
)

from .monte_carlo import (
    simulate_match,
)

from .odds import (
    implied_probabilities,
    fair_odds,
    expected_value,
)

from .selection import (
    select,
)

from .kelly import (
    quarter_kelly,
)

from .pipeline import (
    Q200Pipeline,
)

from .file_pipeline import (
    run_pipeline_from_files,
)

from .analyzer import (
    run_q200_from_files,
)

from .report import (
    REPORT_VERSION,
    build_report,
    report_to_json,
    report_to_text,
)

from .history import (
    HISTORY_SCHEMA_VERSION,
    AnalysisHistory,
)

from .settlement import (
    SETTLEMENT_VERSION,
    settle_analysis_record,
)


__all__ = [
    "TeamStats",
    "ModelSnapshot",
    "OddsInput",
    "AnalysisResult",

    "calculate_lambdas",
    "build_model",

    "poisson_pmf",
    "poisson_score_matrix",
    "poisson_match_probabilities",

    "simulate_match",

    "implied_probabilities",
    "fair_odds",
    "expected_value",

    "select",

    "quarter_kelly",

    "Q200Pipeline",

    "run_pipeline_from_files",

    "run_q200_from_files",

    "REPORT_VERSION",
    "build_report",
    "report_to_json",
    "report_to_text",

    "HISTORY_SCHEMA_VERSION",
    "AnalysisHistory",

    "SETTLEMENT_VERSION",
    "settle_analysis_record",
]
