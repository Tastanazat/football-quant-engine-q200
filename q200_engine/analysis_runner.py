"""
Q200 Engine - Analysis Runner

Q200 V3.1

Amaç
-----

Q200 analizleri için tek bir üst seviye giriş noktası
sağlamak.

Desteklenen girişler:

1. TeamStats
2. FiveSourceMatchInput

TeamStats akışı:

TeamStats
    ↓
Q200Pipeline
    ↓
MODEL
    ↓
MODEL LOCK
    ↓
STRESS TEST
    ↓
ODDS
    ↓
NO-VIG
    ↓
FAIR ODDS
    ↓
BASELINE EV
    ↓
PESSIMISTIC EV
    ↓
SELECTION
    ↓
KELLY

Five Source akışı:

FiveSourceMatchInput
    ↓
Five Source Pipeline
    ↓
CanonicalMatchData
    ↓
Validation
    ↓
TeamStats
    ↓
Q200Pipeline
    ↓
MODEL LOCK
    ↓
ODDS ANALYSIS

KRİTİK KURAL
------------

Bu katman model hesaplamaz.

Model hesaplama Q200Pipeline tarafından yapılır.

Five Source dönüşümü five_source_pipeline tarafından yapılır.

Odds model oluşturulmadan önce kullanılmaz.

Odds modeli değiştiremez.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .pipeline import (
    Q200Pipeline,
)
from .schema import (
    AnalysisResult,
    TeamStats,
)
from .five_source_pipeline import (
    run_five_source_analysis,
)
from .ingestion.models import (
    FiveSourceMatchInput,
)


RUNNER_VERSION = "Q200-ANALYSIS-RUNNER-V2"


# =========================================================
# RESULT
# =========================================================


@dataclass(frozen=True)
class AnalysisRun:
    """
    Tek bir Q200 analiz çalışmasının sonucu.

    raw_result:
        Mevcut Q200 AnalysisResult.

    metadata:
        Çalıştırma bilgileri.
    """

    result: AnalysisResult
    metadata: dict[str, Any]


# =========================================================
# VALIDATION HELPERS
# =========================================================


def _validate_bankroll(
    bankroll: float,
) -> float:
    """
    Bankroll değerini doğrular.
    """

    try:
        value = float(bankroll)

    except (TypeError, ValueError) as exc:

        raise ValueError(
            "bankroll sayısal olmalıdır."
        ) from exc

    if value <= 0:

        raise ValueError(
            "bankroll pozitif olmalıdır."
        )

    return value


def _validate_odds(
    odds: dict[str, float],
) -> dict[str, float]:
    """
    Odds sözlüğünü normalize eder.

    Pipeline'daki aynı doğrulama kurallarını
    burada önceden kontrol eder.

    Model bu aşamada oluşturulmaz.
    """

    if not isinstance(
        odds,
        dict,
    ):

        raise TypeError(
            "odds dictionary olmalıdır."
        )

    if not odds:

        raise ValueError(
            "odds boş olamaz."
        )

    normalized: dict[str, float] = {}

    for outcome, odd in odds.items():

        key = str(
            outcome
        ).upper()

        try:

            value = float(
                odd
            )

        except (TypeError, ValueError) as exc:

            raise ValueError(
                f"Geçersiz odds: "
                f"{outcome}={odd}"
            ) from exc

        if value <= 1.0:

            raise ValueError(
                f"Odds 1.0'dan büyük "
                f"olmalıdır: {outcome}"
            )

        normalized[key] = value

    return normalized


def _validate_five_source_input(
    data: FiveSourceMatchInput,
) -> None:
    """
    FiveSourceMatchInput tipini doğrular.
    """

    if not isinstance(
        data,
        FiveSourceMatchInput,
    ):

        raise TypeError(
            "data FiveSourceMatchInput "
            "olmalıdır."
        )


# =========================================================
# TEAMSTATS ANALYSIS
# =========================================================


def run_analysis(
    *,
    stats: TeamStats,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisRun:
    """
    Q200 V3.1 TeamStats tabanlı tam analiz çalıştırıcısı.

    Model önce oluşturulur.

    Pipeline modeli LOCK eder.

    Daha sonra odds analizi yapılır.

    Odds model oluşturma aşamasına girmez.
    """

    if not isinstance(
        stats,
        TeamStats,
    ):

        raise TypeError(
            "stats TeamStats olmalıdır."
        )

    normalized_odds = _validate_odds(
        odds
    )

    validated_bankroll = (
        _validate_bankroll(
            bankroll
        )
    )

    pipeline = Q200Pipeline(
        stats
    )

    if not pipeline.model_locked:

        raise RuntimeError(
            "Q200 modeli LOCK edilmedi."
        )

    result = pipeline.analyze_odds(
        odds=normalized_odds,
        bankroll=validated_bankroll,
        uncertainty=uncertainty,
    )

    if not result.snapshot.locked:

        raise RuntimeError(
            "Analiz sonucu LOCK edilmiş "
            "model içermiyor."
        )

    return AnalysisRun(
        result=result,
        metadata={
            "runner_version": RUNNER_VERSION,
            "pipeline_version": (
                pipeline.VERSION
            ),
            "input_type": "TeamStats",
            "model_locked": True,
            "odds_used_after_model_lock": True,
            "uncertainty": uncertainty,
        },
    )


# =========================================================
# EXISTING PIPELINE ANALYSIS
# =========================================================


def run_from_pipeline(
    *,
    pipeline: Q200Pipeline,
    odds: dict[str, float],
    bankroll: float,
    uncertainty: str = "MEDIUM",
) -> AnalysisRun:
    """
    Önceden oluşturulmuş Q200Pipeline üzerinden
    analiz çalıştırır.

    Pipeline'ın mevcut snapshot'ı korunur.

    Özellikle test ve üst seviye entegrasyonlarda
    kullanılabilir.
    """

    if not isinstance(
        pipeline,
        Q200Pipeline,
    ):

        raise TypeError(
            "pipeline Q200Pipeline "
            "olmalıdır."
        )

    if not pipeline.model_locked:

        raise RuntimeError(
            "Pipeline modeli "
            "LOCK edilmemiş."
        )

    normalized_odds = _validate_odds(
        odds
    )

    validated_bankroll = (
        _validate_bankroll(
            bankroll
        )
    )

    snapshot_before = (
        pipeline.snapshot
    )

    result = pipeline.analyze_odds(
        odds=normalized_odds,
        bankroll=validated_bankroll,
        uncertainty=uncertainty,
    )

    if pipeline.snapshot != snapshot_before:

        raise RuntimeError(
            "Analiz sırasında model "
            "snapshot değişti."
        )

    if not result.snapshot.locked:

        raise RuntimeError(
            "Analiz sonucu LOCK edilmiş "
            "model içermiyor."
        )

    return AnalysisRun(
        result=result,
        metadata={
            "runner_version": RUNNER_VERSION,
            "pipeline_version": (
                pipeline.VERSION
            ),
            "input_type": "ExistingPipeline",
            "model_locked": True,
            "odds_used_after_model_lock": True,
            "uncertainty": uncertainty,
            "existing_pipeline": True,
        },
    )


# =========================================================
# FIVE SOURCE ANALYSIS
# =========================================================


def run_five_source(
    *,
    data: FiveSourceMatchInput,
    bankroll: float,
    market: str = "1X2",
    uncertainty: str = "MEDIUM",
) -> AnalysisRun:
    """
    FiveSourceMatchInput üzerinden tam Q200 analizini
    çalıştırır.

    Bu fonksiyon Five Source mantığını yeniden yazmaz.

    Mevcut:

        five_source_pipeline.run_five_source_analysis

    fonksiyonunu kullanır.

    Akış:

        StatsHub HOME
        StatsHub AWAY
        SoccerSTATS
        PPI
        Odds
             ↓
        FiveSourceMatchInput
             ↓
        Five Source Pipeline
             ↓
        CanonicalMatchData
             ↓
        TeamStats
             ↓
        Q200 Model
             ↓
        MODEL LOCK
             ↓
        Odds Analysis
    """

    _validate_five_source_input(
        data
    )

    validated_bankroll = (
        _validate_bankroll(
            bankroll
        )
    )

    result = run_five_source_analysis(
        data,
        market=market,
        bankroll=validated_bankroll,
        uncertainty=uncertainty,
    )

    if not result.snapshot.locked:

        raise RuntimeError(
            "Five Source analizi LOCK edilmiş "
            "model içermiyor."
        )

    return AnalysisRun(
        result=result,
        metadata={
            "runner_version": RUNNER_VERSION,
            "pipeline_version": (
                "Q200-FIVE-SOURCE-PIPELINE-V1"
            ),
            "input_type": (
                "FiveSourceMatchInput"
            ),
            "market": market,
            "model_locked": True,
            "odds_used_after_model_lock": True,
            "uncertainty": uncertainty,
            "five_source": True,
        },
    )


# =========================================================
# GENERIC ENTRY POINT
# =========================================================


def run(
    *,
    stats: TeamStats | None = None,
    five_source_data: FiveSourceMatchInput | None = None,
    odds: dict[str, float] | None = None,
    bankroll: float,
    uncertainty: str = "MEDIUM",
    market: str = "1X2",
) -> AnalysisRun:
    """
    Q200 için birleşik üst seviye giriş noktası.

    İki giriş desteklenir:

    1. TeamStats + odds
    2. FiveSourceMatchInput

    Aynı anda iki farklı input verilmesine izin verilmez.
    """

    has_stats = (
        stats is not None
    )

    has_five_source = (
        five_source_data is not None
    )

    if has_stats and has_five_source:

        raise ValueError(
            "stats ve five_source_data "
            "aynı anda kullanılamaz."
        )

    if not has_stats and not has_five_source:

        raise ValueError(
            "stats veya five_source_data "
            "verilmelidir."
        )

    # -----------------------------------------------------
    # Five Source
    # -----------------------------------------------------

    if has_five_source:

        return run_five_source(
            data=five_source_data,
            bankroll=bankroll,
            market=market,
            uncertainty=uncertainty,
        )

    # -----------------------------------------------------
    # TeamStats
    # -----------------------------------------------------

    if odds is None:

        raise ValueError(
            "TeamStats analizi için "
            "odds gereklidir."
        )

    return run_analysis(
        stats=stats,
        odds=odds,
        bankroll=bankroll,
        uncertainty=uncertainty,
    )


# =========================================================
# EXPORTS
# =========================================================


__all__ = [
    "RUNNER_VERSION",
    "AnalysisRun",
    "run_analysis",
    "run_from_pipeline",
    "run_five_source",
    "run",
]
