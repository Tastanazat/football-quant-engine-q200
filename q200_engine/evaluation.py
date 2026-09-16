"""
Q200 Engine - Evaluation Report

Q200 V3.1

History, Settlement, Performance ve Calibration katmanlarını tek bir
salt-okunur değerlendirme çıktısında birleştirir.

Bu katman:
- Model hesabı yapmaz.
- Odds hesabı yapmaz.
- Selection değiştirmez.
- Stake değiştirmez.
- History verisini değiştirmez.
- Yalnızca mevcut sonuçları toplar ve raporlar.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from .calibration import (
    CalibrationBucket,
    CalibrationSummary,
    calibration_buckets,
    calibration_by_market,
    calibration_summary,
)
from .performance import (
    MarketPerformance,
    PerformanceSummary,
    market_performance,
    summarize_history,
)


EVALUATION_VERSION = "Q200-EVALUATION-V1"


@dataclass(frozen=True)
class EvaluationReport:
    """Q200 History değerlendirmesinin birleşik çıktısı."""

    evaluation_version: str
    performance_version: str
    calibration_version: str

    performance: PerformanceSummary
    calibration: CalibrationSummary
    market_performance: dict[str, MarketPerformance]
    market_calibration: dict[str, CalibrationSummary]
    calibration_buckets: list[CalibrationBucket]


def build_evaluation(
    history,
    *,
    starting_bankroll: float = 0.0,
    bucket_count: int = 10,
) -> EvaluationReport:
    """History verisinden tek bir Q200 evaluation raporu üretir."""

    performance = summarize_history(
        history,
        starting_bankroll=starting_bankroll,
    )

    calibration = calibration_summary(
        history
    )

    market_results = market_performance(
        history
    )

    market_calibration_results = calibration_by_market(
        history
    )

    buckets = calibration_buckets(
        history,
        bucket_count=bucket_count,
    )

    from .performance import PERFORMANCE_VERSION
    from .calibration import CALIBRATION_VERSION

    return EvaluationReport(
        evaluation_version=EVALUATION_VERSION,
        performance_version=PERFORMANCE_VERSION,
        calibration_version=CALIBRATION_VERSION,
        performance=performance,
        calibration=calibration,
        market_performance=market_results,
        market_calibration=market_calibration_results,
        calibration_buckets=buckets,
    )


def evaluation_to_dict(
    evaluation: EvaluationReport,
) -> dict[str, Any]:
    """EvaluationReport'u JSON uyumlu dictionary'ye çevirir."""

    if not isinstance(
        evaluation,
        EvaluationReport,
    ):
        raise TypeError(
            "evaluation EvaluationReport olmalıdır."
        )

    return asdict(
        evaluation
    )


def evaluation_to_json(
    evaluation: EvaluationReport,
    *,
    indent: int = 2,
) -> str:
    """EvaluationReport'u standart JSON metnine çevirir."""

    if isinstance(
        indent,
        bool,
    ) or not isinstance(
        indent,
        int,
    ):
        raise TypeError(
            "indent integer olmalıdır."
        )

    if indent < 0:
        raise ValueError(
            "indent negatif olamaz."
        )

    return json.dumps(
        evaluation_to_dict(
            evaluation
        ),
        ensure_ascii=False,
        indent=indent,
        sort_keys=False,
    )


def evaluation_to_text(
    evaluation: EvaluationReport,
) -> str:
    """EvaluationReport için kısa, okunabilir metin raporu."""

    if not isinstance(
        evaluation,
        EvaluationReport,
    ):
        raise TypeError(
            "evaluation EvaluationReport olmalıdır."
        )

    performance = evaluation.performance
    calibration = evaluation.calibration

    lines = [
        "Q200 V3.1 EVALUATION RAPORU",
        "=" * 32,
        f"Evaluation Version : {evaluation.evaluation_version}",
        f"Performance Version: {evaluation.performance_version}",
        f"Calibration Version: {evaluation.calibration_version}",
        "",
        "PERFORMANCE",
        f"Analysis Records   : {performance.total_analysis_records}",
        f"Completed Matches  : {performance.completed_matches}",
        f"Settled Matches    : {performance.settled_matches}",
        f"Total Bets         : {performance.total_bets}",
        f"Wins               : {performance.wins}",
        f"Losses             : {performance.losses}",
        f"Voids              : {performance.voids}",
        f"Total Stake        : {performance.total_stake:.2f}",
        f"Total Profit       : {performance.total_profit:.2f}",
        f"ROI                : {performance.roi:.2%}",
        f"Hit Rate           : {performance.hit_rate:.2%}",
        f"Starting Bankroll  : {performance.starting_bankroll:.2f}",
        f"Ending Bankroll    : {performance.ending_bankroll:.2f}",
        "",
        "CALIBRATION",
        f"Total Predictions  : {calibration.total_predictions}",
        f"Evaluated          : {calibration.evaluated_predictions}",
        f"Voids              : {calibration.void_predictions}",
        f"Missing Probability: {calibration.missing_probability_predictions}",
        f"Brier Score        : {calibration.brier_score:.6f}",
        f"Log Loss           : {calibration.log_loss:.6f}",
        f"Mean Probability   : {calibration.mean_predicted_probability:.2%}",
        f"Empirical Win Rate : {calibration.empirical_win_rate:.2%}",
        f"Coverage           : {calibration.coverage:.2%}",
    ]

    if evaluation.market_performance:
        lines.extend(
            [
                "",
                "MARKET PERFORMANCE",
            ]
        )

        for market, result in (
            evaluation.market_performance.items()
        ):
            lines.append(
                f"{market:<15} bets={result.total_bets} "
                f"W={result.wins} L={result.losses} V={result.voids} "
                f"ROI={result.roi:.2%}"
            )

    if evaluation.market_calibration:
        lines.extend(
            [
                "",
                "MARKET CALIBRATION",
            ]
        )

        for market, result in (
            evaluation.market_calibration.items()
        ):
            lines.append(
                f"{market:<15} n={result.evaluated_predictions} "
                f"Brier={result.brier_score:.6f} "
                f"LogLoss={result.log_loss:.6f} "
                f"Pred={result.mean_predicted_probability:.2%} "
                f"Actual={result.empirical_win_rate:.2%}"
            )

    return "\n".join(
        lines
    )
