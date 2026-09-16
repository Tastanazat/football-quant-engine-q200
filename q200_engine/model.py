"""
Q200 Engine - Model Layer

Q200 V3.1

Stage 1:

Statistics
    ↓
Lambda
    ↓
Poisson
    ↓
Monte Carlo
    ↓
Model Probabilities
    ↓
LOCK

KRİTİK KURAL:
Odds bu katmanda KULLANILMAZ.
"""

from __future__ import annotations

from math import isfinite
from typing import Optional

from .monte_carlo import simulate_match
from .poisson_model import (
    poisson_match_probabilities,
    poisson_score_matrix,
)
from .schema import ModelSnapshot, TeamStats


# =========================================================
# MODEL WEIGHTS
# =========================================================

HOME_GF_WEIGHT = 0.35
AWAY_GA_WEIGHT = 0.35
HOME_XG_WEIGHT = 0.15
AWAY_XGA_WEIGHT = 0.15

AWAY_GF_WEIGHT = 0.35
HOME_GA_WEIGHT = 0.35
AWAY_XG_WEIGHT = 0.15
HOME_XGA_WEIGHT = 0.15


# =========================================================
# MONTE CARLO
# =========================================================

MONTE_CARLO_ITERATIONS = 100_000


# =========================================================
# MODEL VERSION
# =========================================================

MODEL_VERSION = "Q200-V3.1"


# =========================================================
# VALIDATION
# =========================================================

def _valid(value: Optional[float]) -> bool:
    """
    Değerin kullanılabilir bir istatistik olup olmadığını kontrol eder.

    Geçerli değer:
        - None değil
        - int veya float
        - finite
        - negatif değil
    """

    return (
        value is not None
        and isinstance(value, (int, float))
        and isfinite(float(value))
        and float(value) >= 0
    )


# =========================================================
# WEIGHTED AVERAGE
# =========================================================

def _weighted_average(
    components: list[tuple[Optional[float], float]],
    name: str,
) -> float:
    """
    Mevcut istatistikleri ağırlıklı olarak birleştirir.

    Bir veri eksikse mevcut verilerin ağırlıkları
    kendi aralarında normalize edilir.

    Örnek:

        GF   = 2.0  weight=0.35
        GA   = 1.8  weight=0.35
        xG   = None
        xGA  = 1.4  weight=0.15

    Eksik xG nedeniyle kalan ağırlıklar normalize edilir.
    """

    available = [
        (float(value), weight)
        for value, weight in components
        if _valid(value)
    ]

    if not available:
        raise ValueError(
            f"{name} lambda için yeterli veri bulunamadı."
        )

    weight_sum = sum(
        weight
        for _, weight in available
    )

    if weight_sum <= 0:
        raise ValueError(
            f"{name} lambda ağırlık toplamı geçersiz."
        )

    result = sum(
        value * (weight / weight_sum)
        for value, weight in available
    )

    return round(result, 12)


# =========================================================
# LAMBDA CALCULATION
# =========================================================

def calculate_lambdas(
    stats: TeamStats,
) -> tuple[float, float]:
    """
    Q200 V3.1 lambda hesaplama.

    HOME:

        0.35 * Home GF
      + 0.35 * Away GA
      + 0.15 * Home xG
      + 0.15 * Away xGA

    AWAY:

        0.35 * Away GF
      + 0.35 * Home GA
      + 0.15 * Away xG
      + 0.15 * Home xGA

    xG/xGA eksikse mevcut ağırlıklar normalize edilir.

    KRİTİK:
    Odds burada kullanılmaz.
    """

    if not isinstance(stats, TeamStats):
        raise TypeError(
            "stats must be an instance of TeamStats"
        )

    # -----------------------------------------------------
    # HOME LAMBDA
    # -----------------------------------------------------

    lambda_home = _weighted_average(
        [
            (
                stats.home_gf,
                HOME_GF_WEIGHT,
            ),
            (
                stats.away_ga,
                AWAY_GA_WEIGHT,
            ),
            (
                stats.home_xg,
                HOME_XG_WEIGHT,
            ),
            (
                stats.away_xga,
                AWAY_XGA_WEIGHT,
            ),
        ],
        "HOME",
    )

    # -----------------------------------------------------
    # AWAY xG
    # -----------------------------------------------------
    #
    # Legacy uyumluluk:
    #
    # Eski 7-parametreli TeamStats yapısında
    # away_xg bulunmadığında away_xga son alan olabilir.
    #
    # Bu durumda mevcut away_xga değeri fallback olarak
    # away_xg tarafında da kullanılabilir.
    # -----------------------------------------------------

    away_xg = (
        stats.away_xg
        if _valid(stats.away_xg)
        else stats.away_xga
    )

    # -----------------------------------------------------
    # AWAY LAMBDA
    # -----------------------------------------------------

    lambda_away = _weighted_average(
        [
            (
                stats.away_gf,
                AWAY_GF_WEIGHT,
            ),
            (
                stats.home_ga,
                HOME_GA_WEIGHT,
            ),
            (
                away_xg,
                AWAY_XG_WEIGHT,
            ),
            (
                stats.home_xga,
                HOME_XGA_WEIGHT,
            ),
        ],
        "AWAY",
    )

    # -----------------------------------------------------
    # SAFETY FLOOR
    # -----------------------------------------------------

    lambda_home = max(
        0.01,
        float(lambda_home),
    )

    lambda_away = max(
        0.01,
        float(lambda_away),
    )

    return lambda_home, lambda_away


# =========================================================
# BUILD MODEL
# =========================================================

def build_model(
    stats: TeamStats,
    max_goals: int = 10,
) -> ModelSnapshot:
    """
    Statistics -> LOCKED ModelSnapshot.

    Pipeline:

        STATS
          ↓
        LAMBDA
          ↓
        POISSON SCORE MATRIX
          ↓
        POISSON PROBABILITIES
          ↓
        MONTE CARLO 100K
          ↓
        MODEL SNAPSHOT
          ↓
        LOCK 🔒

    KRİTİK KURAL:

        Odds bu fonksiyona girmez.

    Böylece oranların model oluşturma aşamasını
    etkilemesi mümkün değildir.
    """

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not isinstance(stats, TeamStats):
        raise TypeError(
            "stats must be an instance of TeamStats"
        )

    if not isinstance(max_goals, int):
        raise TypeError(
            "max_goals integer olmalıdır."
        )

    if max_goals < 1:
        raise ValueError(
            "max_goals en az 1 olmalıdır."
        )

    # -----------------------------------------------------
    # STEP 1
    # -----------------------------------------------------

    lambda_home, lambda_away = calculate_lambdas(
        stats
    )

    # -----------------------------------------------------
    # STEP 2
    # POISSON SCORE MATRIX
    # -----------------------------------------------------

    score_matrix = poisson_score_matrix(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    # -----------------------------------------------------
    # STEP 3
    # POISSON MODEL PROBABILITIES
    # -----------------------------------------------------

    probabilities = poisson_match_probabilities(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    # -----------------------------------------------------
    # STEP 4
    # MONTE CARLO
    # -----------------------------------------------------

    monte_carlo = simulate_match(
        lambda_home,
        lambda_away,
        iterations=MONTE_CARLO_ITERATIONS,
    )

    # -----------------------------------------------------
    # STEP 5
    # LOCK MODEL
    # -----------------------------------------------------

    snapshot = ModelSnapshot(
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        probabilities=probabilities,
        score_matrix=score_matrix,
        monte_carlo_probabilities=monte_carlo,
        max_goals=max_goals,
        model_version=MODEL_VERSION,
        locked=True,
    )

    return snapshot
