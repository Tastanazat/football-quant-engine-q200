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

from .statshub_ocr import (
    STATSHUB_OCR_VERSION,
    STAT_LABELS,
    canonical_stat_name,
    parse_number,
    extract_numbers,
    parse_statshub_text,
    parse_statshub_table_text,
    flatten_statshub_summary,
    ocr_image_to_text,
    create_statshub_review,
)

from .statshub_feature_adapter import (
    STATSHUB_FEATURE_ADAPTER_VERSION,
    STATSHUB_FOR_TO_FEATURE,
    statshub_pair_to_feature_input,
    build_features_from_statshub_pair,
    build_features_from_approved_reviews,
)

from .feature_engine import (
    FEATURE_ENGINE_VERSION,
    FeatureSet,
    build_features,
    feature_set_to_dict,
)

from .feature_quality import (
    FEATURE_QUALITY_VERSION,
    DEFAULT_CORRELATION_THRESHOLD,
    FeaturePair,
    FeatureQuality,
    FeatureQualityReport,
    discover_features,
    assess_feature_quality,
    calculate_feature_correlation,
    calculate_all_correlations,
    find_redundant_features,
    build_feature_quality_report,
    feature_quality_to_dict,
)

from .feature_selection import (
    FEATURE_SELECTION_VERSION,
    DEFAULT_MAX_MISSING_RATE,
    DEFAULT_REDUNDANCY_CORRELATION,
    DECISIONS,
    FeatureSelectionDecision,
    FeatureSelectionReport,
    discover_selection_candidates,
    select_features,
    selected_feature_names,
    feature_selection_to_dict,
    feature_selection_summary,
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

    "run_q200_from_files",

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
    "MarketPerformance",
    "PerformanceSummary",
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

    "STATSHUB_OCR_VERSION",
    "STAT_LABELS",
    "canonical_stat_name",
    "parse_number",
    "extract_numbers",
    "parse_statshub_text",
    "parse_statshub_table_text",
    "flatten_statshub_summary",
    "ocr_image_to_text",
    "create_statshub_review",

    "STATSHUB_FEATURE_ADAPTER_VERSION",
    "STATSHUB_FOR_TO_FEATURE",
    "statshub_pair_to_feature_input",
    "build_features_from_statshub_pair",
    "build_features_from_approved_reviews",

    "FEATURE_ENGINE_VERSION",
    "FeatureSet",
    "build_features",
    "feature_set_to_dict",

    "FEATURE_QUALITY_VERSION",
    "DEFAULT_CORRELATION_THRESHOLD",
    "FeaturePair",
    "FeatureQuality",
    "FeatureQualityReport",
    "discover_features",
    "assess_feature_quality",
    "calculate_feature_correlation",
    "calculate_all_correlations",
    "find_redundant_features",
    "build_feature_quality_report",
    "feature_quality_to_dict",

    "FEATURE_SELECTION_VERSION",
    "DEFAULT_MAX_MISSING_RATE",
    "DEFAULT_REDUNDANCY_CORRELATION",
    "DECISIONS",
    "FeatureSelectionDecision",
    "FeatureSelectionReport",
    "discover_selection_candidates",
    "select_features",
    "selected_feature_names",
    "feature_selection_to_dict",
    "feature_selection_summary",

    "DATASET_BACKTEST_VERSION",
    "DatasetBacktestItem",
    "DatasetBacktestSummary",
    "DatasetBacktestRunner",
    "read_dataset_file",
    "run_dataset_backtest",
]
