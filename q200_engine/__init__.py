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
    run_pipeline_from_reviews,
)

from .analyzer import (
    run_q200_from_files,
)

from .statistics_reader import (
    read_statistics_review,
)

from .statistics_loader import (
    load_team_stats_from_reviews,
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

from .calibration import (
    CALIBRATION_VERSION,
    CalibrationSummary,
    CalibrationBucket,
    CalibrationObservation,
    collect_observations,
    calibration_summary,
    calibration_buckets,
    calibration_by_market,
)

from .performance import (
    PERFORMANCE_VERSION,
    PerformanceSummary,
    MarketPerformance,
    summarize_history,
    market_performance,
)

from .evaluation import (
    EVALUATION_VERSION,
    EvaluationReport,
    build_evaluation,
    evaluation_to_dict,
    evaluation_to_json,
    evaluation_to_text,
)

from .data_review import (
    DATA_REVIEW_VERSION,
    SOURCE_TYPES,
    VALUE_STATUSES,
    ReviewField,
    DataReview,
    create_review,
    update_review_field,
    approve_review,
    revoke_review,
    reviewed_values,
    review_to_dict,
)

from .dataset_backtest import (
    DATASET_BACKTEST_VERSION,
    DatasetBacktestItem,
    DatasetBacktestSummary,
    DatasetBacktestRunner,
    read_dataset_file,
    run_dataset_backtest,
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
    "run_pipeline_from_reviews",

    "run_q200_from_files",

    "read_statistics_review",
    "load_team_stats_from_reviews",

    "REPORT_VERSION",
    "build_report",
    "report_to_json",
    "report_to_text",

    "HISTORY_SCHEMA_VERSION",
    "AnalysisHistory",

    "SETTLEMENT_VERSION",
    "settle_analysis_record",

    "CALIBRATION_VERSION",
    "CalibrationSummary",
    "CalibrationBucket",
    "CalibrationObservation",
    "collect_observations",
    "calibration_summary",
    "calibration_buckets",
    "calibration_by_market",

    "PERFORMANCE_VERSION",
    "PerformanceSummary",
    "MarketPerformance",
    "summarize_history",
    "market_performance",

    "EVALUATION_VERSION",
    "EvaluationReport",
    "build_evaluation",
    "evaluation_to_dict",
    "evaluation_to_json",
    "evaluation_to_text",

    "DATA_REVIEW_VERSION",
    "SOURCE_TYPES",
    "VALUE_STATUSES",
    "ReviewField",
    "DataReview",
    "create_review",
    "update_review_field",
    "approve_review",
    "revoke_review",
    "reviewed_values",
    "review_to_dict",

    "DATASET_BACKTEST_VERSION",
    "DatasetBacktestItem",
    "DatasetBacktestSummary",
    "DatasetBacktestRunner",
    "read_dataset_file",
    "run_dataset_backtest",
]
