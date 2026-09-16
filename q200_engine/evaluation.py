"""
Q200 Engine - Evaluation Report

Q200 V3.1

History içindeki sonuçlanmış Q200 analizlerini tek bir standart
performans ve calibration raporunda birleştirir.

Bu katman:
- Model hesabını değiştirmez.
- Odds hesabını değiştirmez.
- Selection üretmez.
- Settlement verisini değiştirmez.
- Sadece kayıtlı Performance ve Calibration verilerini birleştirir.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from .calibration import (
    CALIBRATION_VERSION,
    CalibrationBucket,
    CalibrationSummary,
    calibration_buckets,
    calibration_by_market,
    calibration_summary,
)

from .performance import (
    PERFORMANCE_VERSION,
    MarketPerformance,
    PerformanceSummary,
    market_performance,
    summarize_history,
)


EVALUATION_VERSION = "Q200-EVALUATION-V1"


@dataclass(frozen=True)
class EvaluationReport:
    """Performance + calibration birleşik değerlendirme raporu."""

    evaluation_version: str
    performance_version: str
    calibration_version: str

    performance: PerformanceSummary
    market_performance: dict[str, MarketPerformance]

    calibration: CalibrationSummary
   
