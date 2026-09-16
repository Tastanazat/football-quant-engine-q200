"""
Q200 Engine - Model Layer

Q200 V3.1
"""

from __future__ import annotations

from math import isfinite
from typing import Optional

from .schema import TeamStats, ModelSnapshot
from .poisson_model import poisson_score_matrix
from .monte_carlo import simulate_match


# =========================================================
# CONSTANTS
# =========================================================

HOME_GF_WEIGHT = 0.35
AWAY_GA_WEIGHT = 0.35
HOME_XG_WEIGHT = 0.15
AWAY_XGA_WEIGHT = 0.15

AWAY_GF_WEIGHT = 0.35
HOME_GA_WEIGHT = 0.35
AWAY_XG_WEIGHT = 0.15
HOME_XGA_WEIGHT = 0.15

MONTE_CARLO_ITERATIONS = 100_000
MONTE_CARLO_SEED = 42


# =========================================================
# VALIDATION
# =========================================================

def _valid(value: Optional[float]) -> bool:
    """
    Değerin kullanılabilir olup olmadığını kontrol eder.
    """

    return (
        value is not None
        and isinstance(value, (int, float))
        and isfinite(float(value))
        and float(value) >= 0
    )


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

    xG/xGA eksikse mevcut değerler üzerinden
    ağırlıklar yeniden normalize edilir.
    """

    if not isinstance(stats, TeamStats):
        raise TypeError(
            "stats must be an instance of TeamStats"
        )

    # =====================================================
    # HOME
    # =====================================================

    home_components = [
        (stats.home_gf, HOME_GF_WEIGHT),
        (stats.away_ga, AWAY_GA_WEIGHT),
        (stats.home_xg, HOME_XG_WEIGHT),
        (stats.away_xga, AWAY_XGA_WEIGHT),
    ]

    home_available = [
        (value, weight)
        for value, weight in home_components
        if _valid(value)
    ]

    if not home_available:
        raise ValueError(
            "HOME lambda için yeterli veri bulunamadı."
        )

    home_weight_sum = sum(
        weight
        for _, weight in home_available
    )

    lambda_home = sum(
        float(value) * (weight / home_weight_sum)
        for value, weight in home_available
    )

    # =====================================================
    # AWAY
    # =====================================================

    # Yeni standart away_xg mevcutsa onu kullan.
    #
    # Legacy 7 parametreli yapılarda away_xga
    # fallback olarak kullanılır.

    away_xg = (
        stats.away_xg
        if _valid(stats.away_xg)
        else stats.away_xga
    )

    away_components = [
        (stats.away_gf, AWAY_GF_WEIGHT),
        (stats.home_ga, HOME_GA_WEIGHT),
        (away_xg, AWAY_XG_WEIGHT),
        (stats.home_xga, HOME_XGA_WEIGHT),
    ]

    away_available = [
        (value, weight)
        for value, weight in away_components
        if _valid(value)
    ]

    if not away_available:
        raise ValueError(
            "AWAY lambda için yeterli veri bulunamadı."
        )

    away_weight_sum = sum(
        weight
        for _, weight in away_available
    )

    lambda_away = sum(
        float(value) * (weight / away_weight_sum)
        for value, weight in away_available
    )

    return (
        round(lambda_home, 12),
        round(lambda_away, 12),
    )


# =========================================================
# MODEL BUILD
# =========================================================

def build_model(
    stats: TeamStats,
    max_goals: int = 10,
) -> ModelSnapshot:
    """
    Q200 V3.1 model oluşturur.

    Akış:

        STATISTICS
            ↓
        LAMBDA
            ↓
        POISSON
            ↓
        MONTE CARLO
            ↓
        MODEL SNAPSHOT
            ↓
        LOCK

    ÖNEMLİ:

    Odds bu fonksiyona girmez.

    Dolayısıyla odds model oluşturma aşamasını
    hiçbir şekilde etkileyemez.
    """

    if not isinstance(stats, TeamStats):
        raise TypeError(
            "stats must be an instance of TeamStats"
        )

    if isinstance(max_goals, bool):
        raise TypeError(
            "max_goals integer olmalıdır."
        )

    if not isinstance(max_goals, int):
        raise TypeError(
            "max_goals integer olmalıdır."
        )

    if max_goals < 1:
        raise ValueError(
            "max_goals en az 1 olmalıdır."
        )

    # =====================================================
    # STEP 1 — LAMBDA
    # =====================================================

    lambda_home, lambda_away = calculate_lambdas(
        stats
    )

    # =====================================================
    # STEP 2 — POISSON SCORE MATRIX
    # =====================================================

    score_matrix = poisson_score_matrix(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    # =====================================================
    # STEP 3 — POISSON PROBABILITIES
    # =====================================================

    probabilities = {
        "HOME": sum(
            score_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(max_goals + 1)
            if h > a
        ),
        "DRAW": sum(
            score_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(max_goals + 1)
            if h == a
        ),
        "AWAY": sum(
            score_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(max_goals + 1)
            if h < a
        ),
    }

    # =====================================================
    # STEP 4 — MONTE CARLO
    # =====================================================

    monte_carlo_probabilities = simulate_match(
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        iterations=MONTE_CARLO_ITERATIONS,
        seed=MONTE_CARLO_SEED,
    )

    # =====================================================
    # STEP 5 — MODEL SNAPSHOT
    # =====================================================

    snapshot = ModelSnapshot(
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        probabilities=probabilities,
        score_matrix=score_matrix,
        monte_carlo_probabilities=(
            monte_carlo_probabilities
        ),
        monte_carlo_iterations=(
            MONTE_CARLO_ITERATIONS
        ),
        max_goals=max_goals,
        model_version="Q200-V3.1",
        locked=True,
    )

    # =====================================================
    # STEP 6 — LOCK VALIDATION
    # =====================================================

    if not snapshot.locked:
        raise RuntimeError(
            "Q200 model LOCK edilemedi."
        )

    return snapshot    # xG alanı olarak kullanılır.
    away_xg = (
        stats.away_xg
        if _valid(stats.away_xg)
        else stats.away_xga
    )

    away_components = [
        (stats.away_gf, AWAY_GF_WEIGHT),
        (stats.home_ga, HOME_GA_WEIGHT),
        (away_xg, AWAY_XG_WEIGHT),
        (stats.home_xga, HOME_XGA_WEIGHT),
    ]

    away_available = [
        (value, weight)
        for value, weight in away_components
        if _valid(value)
    ]

    if not away_available:
        raise ValueError(
            "AWAY lambda için yeterli veri bulunamadı."
        )

    away_weight_sum = sum(
        weight for _, weight in away_available
    )

    lambda_away = sum(
        float(value) * (weight / away_weight_sum)
        for value, weight in away_available
    )

    return (
        round(lambda_home, 12),
        round(lambda_away, 12),
    )


# =========================================================
# MODEL BUILD
# =========================================================

def build_model(
    stats: TeamStats,
    max_goals: int = 10,
) -> ModelSnapshot:
    """
    Model oluşturur ve LOCK eder.

    Odds bu aşamada kullanılmaz.
    """

    if max_goals < 1:
        raise ValueError(
            "max_goals en az 1 olmalıdır."
        )

    lambda_home, lambda_away = calculate_lambdas(stats)

    score_matrix = poisson_score_matrix(
        lambda_home,
        lambda_away,
        max_goals=max_goals,
    )

    probabilities = {
        "HOME": sum(
            score_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(max_goals + 1)
            if h > a
        ),
        "DRAW": sum(
            score_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(max_goals + 1)
            if h == a
        ),
        "AWAY": sum(
            score_matrix[h][a]
            for h in range(max_goals + 1)
            for a in range(max_goals + 1)
            if h < a
        ),
    }

    return ModelSnapshot(
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        probabilities=probabilities,
        score_matrix=score_matrix,
        max_goals=max_goals,
        model_version="Q200-V3.1",
        locked=True,
    )
