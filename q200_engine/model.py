"""
Q200 Engine - Model Layer
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, factorial
from typing import Any, Dict, Tuple


# =========================================================
# MODEL SNAPSHOT
# =========================================================

@dataclass
class ModelSnapshot:
    """
    Pipeline tarafından kullanılan immutable model çıktısı.
    """

    lambda_home: float
    lambda_away: float
    probabilities: Dict[str, float]
    score_matrix: list
    max_goals: int = 10
    locked: bool = True

    @property
    def model_locked(self) -> bool:
        return self.locked


# =========================================================
# ATTRIBUTE HELPER
# =========================================================

def _get(
    obj: Any,
    *names: str,
    default: float = 0.0,
) -> float:

    if isinstance(obj, dict):
        for name in names:
            if name in obj and obj[name] is not None:
                return float(obj[name])

        return float(default)

    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)

            if value is not None:
                return float(value)

    return float(default)


# =========================================================
# LAMBDA CALCULATION
# =========================================================

def calculate_lambdas(stats: Any) -> Tuple[float, float]:
    """
    Q200 lambda hesaplama.

    HOME:
        0.35 * Home Home GF
      + 0.35 * Away Away GA
      + 0.15 * Home Home xG
      + 0.15 * Away Away xGA

    AWAY:
        0.35 * Away Away GF
      + 0.35 * Home Home GA
      + 0.15 * Away Away xG
      + 0.15 * Home Home xGA

    xG/xGA mevcut değilse GF/GA ağırlıkları normalize edilir.
    """

    # -----------------------------------------------------
    # HOME
    # -----------------------------------------------------

    home_gf = _get(
        stats,
        "home_home_gf",
        "home_gf",
        "homeGF",
        "home_goals_for",
    )

    home_ga = _get(
        stats,
        "home_home_ga",
        "home_ga",
        "homeGA",
        "home_goals_against",
    )

    home_xg = _get(
        stats,
        "home_home_xg",
        "home_xg",
        "homeXG",
        default=0.0,
    )

    home_xga = _get(
        stats,
        "home_home_xga",
        "home_xga",
        "homeXGA",
        default=0.0,
    )

    # -----------------------------------------------------
    # AWAY
    # -----------------------------------------------------

    away_gf = _get(
        stats,
        "away_away_gf",
        "away_gf",
        "awayGF",
        "away_goals_for",
    )

    away_ga = _get(
        stats,
        "away_away_ga",
        "away_ga",
        "awayGA",
        "away_goals_against",
    )

    away_xg = _get(
        stats,
        "away_away_xg",
        "away_xg",
        "awayXG",
        default=0.0,
    )

    away_xga = _get(
        stats,
        "away_away_xga",
        "away_xga",
        "awayXGA",
        default=0.0,
    )

    # -----------------------------------------------------
    # xG mevcut mu?
    # -----------------------------------------------------

    xg_available = any(
        value > 0
        for value in (
            home_xg,
            home_xga,
            away_xg,
            away_xga,
        )
    )

    # -----------------------------------------------------
    # WITH xG
    # -----------------------------------------------------

    if xg_available:

        lambda_home = (
            0.35 * home_gf
            + 0.35 * away_ga
            + 0.15 * home_xg
            + 0.15 * away_xga
        )

        lambda_away = (
            0.35 * away_gf
            + 0.35 * home_ga
            + 0.15 * away_xg
            + 0.15 * home_xga
        )

    # -----------------------------------------------------
    # WITHOUT xG
    # -----------------------------------------------------

    else:

        lambda_home = (
            0.50 * home_gf
            + 0.50 * away_ga
        )

        lambda_away = (
            0.50 * away_gf
            + 0.50 * home_ga
        )

    lambda_home = max(0.01, float(lambda_home))
    lambda_away = max(0.01, float(lambda_away))

    return lambda_home, lambda_away


# =========================================================
# POISSON
# =========================================================

def poisson_pmf(k: int, lam: float) -> float:

    if k < 0:
        return 0.0

    return (
        exp(-lam)
        * (lam ** k)
        / factorial(k)
    )


# =========================================================
# SCORE MATRIX
# =========================================================

def build_score_matrix(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
):

    home_probs = [
        poisson_pmf(i, lambda_home)
        for i in range(max_goals + 1)
    ]

    away_probs = [
        poisson_pmf(i, lambda_away)
        for i in range(max_goals + 1)
    ]

    matrix = []

    for home_goals in range(max_goals + 1):

        row = []

        for away_goals in range(max_goals + 1):

            probability = (
                home_probs[home_goals]
                * away_probs[away_goals]
            )

            row.append(probability)

        matrix.append(row)

    return matrix


# =========================================================
# 1X2 PROBABILITIES
# =========================================================

def probabilities_from_lambdas(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10,
) -> Dict[str, float]:

    matrix = build_score_matrix(
        lambda_home,
        lambda_away,
        max_goals,
    )

    home = 0.0
    draw = 0.0
    away = 0.0

    for h in range(max_goals + 1):

        for a in range(max_goals + 1):

            probability = matrix[h][a]

            if h > a:
                home += probability

            elif h == a:
                draw += probability

            else:
                away += probability

    total = home + draw + away

    if total <= 0:
        raise ValueError(
            "Model probabilities could not be calculated."
        )

    return {
        "HOME": home / total,
        "DRAW": draw / total,
        "AWAY": away / total,
    }


# =========================================================
# BUILD MODEL
# =========================================================

def build_model(
    stats: Any,
    max_goals: int = 10,
) -> ModelSnapshot:
    """
    Stats -> ModelSnapshot

    KRİTİK:
    Odds burada kullanılmaz.

    Model oluşturulduktan sonra locked=True olur.
    """

    lambda_home, lambda_away = calculate_lambdas(stats)

    probabilities = probabilities_from_lambdas(
        lambda_home,
        lambda_away,
        max_goals,
    )

    score_matrix = build_score_matrix(
        lambda_home,
        lambda_away,
        max_goals,
    )

    return ModelSnapshot(
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        probabilities=probabilities,
        score_matrix=score_matrix,
        max_goals=max_goals,
        locked=True,
    )


# =========================================================
# COMPATIBILITY
# =========================================================

def model_probabilities(
    stats: Any,
) -> Dict[str, float]:

    snapshot = build_model(stats)

    return snapshot.probabilities
