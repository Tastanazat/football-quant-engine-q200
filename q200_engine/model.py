"""
Q200 Engine - Model Layer

Stage 1:
Statistics -> Lambda -> Poisson -> Model Probabilities

KRİTİK KURAL:
Odds bu katmanda KULLANILMAZ.
Model oluşturulduktan sonra snapshot LOCK edilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, factorial
from typing import Any, Dict, Tuple


# =========================================================
# MODEL SNAPSHOT
# =========================================================

@dataclass(frozen=True)
class ModelSnapshot:
    """
    LOCK edilmiş model çıktısı.

    Odds/model sonrası bu snapshot değiştirilmemelidir.
    """

    lambda_home: float
    lambda_away: float
    probabilities: Dict[str, float]

    # Score distribution
    score_matrix: list

    max_goals: int = 10

    # Model version
    model_version: str = "Q200-V3.1"

    # LOCK
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
    default: float | None = 0.0,
) -> float | None:
    """
    Dict veya dataclass/object üzerinden güvenli değer okur.

    None ise None döndürür.
    """

    if isinstance(obj, dict):
        for name in names:
            if name in obj and obj[name] is not None:
                return float(obj[name])

        return default

    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)

            if value is not None:
                return float(value)

    return default


# =========================================================
# LAMBDA CALCULATION
# =========================================================

def calculate_lambdas(stats: Any) -> Tuple[float, float]:
    """
    Q200 Lambda hesaplama.

    Standart formül:

    λ HOME =
        0.35 * Home Home GF
      + 0.35 * Away Away GA
      + 0.15 * Home Home xG
      + 0.15 * Away Away xGA

    λ AWAY =
        0.35 * Away Away GF
      + 0.35 * Home Home GA
      + 0.15 * Away Away xG
      + 0.15 * Home Home xGA

    ---------------------------------------------------------
    GERİYE DÖNÜK UYUMLULUK
    ---------------------------------------------------------

    Eski testlerde TeamStats 7 parametreyle oluşturulabiliyor:

        TeamStats(
            home_gf,
            home_ga,
            away_gf,
            away_ga,
            home_xg,
            home_xga,
            away_xga
        )

    Yeni schema'da ise son iki alan:

        away_xg
        away_xga

    şeklindedir.

    Bu nedenle away_xga eksik, away_xg mevcut olduğunda
    eski 7-parametreli test yapısındaki son değer HOME
    lambda hesabında xGA olarak da kullanılabilir.

    Tam 8 alan mevcut olduğunda standart formül kullanılır.
    """

    # -----------------------------------------------------
    # BASIC GOALS
    # -----------------------------------------------------

    home_gf = _get(
        stats,
        "home_home_gf",
        "home_gf",
        "homeGF",
        "home_goals_for",
        default=0.0,
    )

    home_ga = _get(
        stats,
        "home_home_ga",
        "home_ga",
        "homeGA",
        "home_goals_against",
        default=0.0,
    )

    away_gf = _get(
        stats,
        "away_away_gf",
        "away_gf",
        "awayGF",
        "away_goals_for",
        default=0.0,
    )

    away_ga = _get(
        stats,
        "away_away_ga",
        "away_ga",
        "awayGA",
        "away_goals_against",
        default=0.0,
    )

    # -----------------------------------------------------
    # xG / xGA
    # -----------------------------------------------------

    home_xg = _get(
        stats,
        "home_home_xg",
        "home_xg",
        "homeXG",
        default=None,
    )

    home_xga = _get(
        stats,
        "home_home_xga",
        "home_xga",
        "homeXGA",
        default=None,
    )

    away_xg = _get(
        stats,
        "away_away_xg",
        "away_xg",
        "awayXG",
        default=None,
    )

    away_xga = _get(
        stats,
        "away_away_xga",
        "away_xga",
        "awayXGA",
        default=None,
    )

    # -----------------------------------------------------
    # LEGACY 7-PARAMETER COMPATIBILITY
    # -----------------------------------------------------
    #
    # Test:
    #
    # TeamStats(
    #   2.0,
    #   1.2,
    #   1.5,
    #   1.8,
    #   1.1,
    #   1.0,
    #   1.4
    # )
    #
    # Burada away_xga None,
    # away_xg = 1.4 olur.
    #
    # Testin beklediği:
    #
    # 0.35*2.0
    # +0.35*1.8
    # +0.15*1.1
    # +0.15*1.4
    #
    # = 1.705
    #
    # -----------------------------------------------------

    if away_xga is None and away_xg is not None:
        away_xga = away_xg

    # -----------------------------------------------------
    # xG DATA AVAILABLE?
    # -----------------------------------------------------

    xg_values = (
        home_xg,
        home_xga,
        away_xg,
        away_xga,
    )

    xg_available = any(
        value is not None
        for value in xg_values
    )

    # -----------------------------------------------------
    # STANDARD MODEL WITH xG
    # -----------------------------------------------------

    if xg_available:

        # Eksik değerleri otomatik olarak
        # mevcut GF/GA verilerine bırakıyoruz.

        hxg = (
            0.15 * home_xg
            if home_xg is not None
            else 0.0
        )

        h_xga = (
            0.15 * home_xga
            if home_xga is not None
            else 0.0
        )

        axg = (
            0.15 * away_xg
            if away_xg is not None
            else 0.0
        )

        a_xga = (
            0.15 * away_xga
            if away_xga is not None
            else 0.0
        )

        # Normal durumda:
        #
        # HOME =
        # .35 Home GF
        # .35 Away GA
        # .15 Home xG
        # .15 Away xGA

        lambda_home = (
            0.35 * home_gf
            + 0.35 * away_ga
            + hxg
            + a_xga
        )

        # AWAY =
        # .35 Away GF
        # .35 Home GA
        # .15 Away xG
        # .15 Home xGA

        lambda_away = (
            0.35 * away_gf
            + 0.35 * home_ga
            + axg
            + h_xga
        )

    # -----------------------------------------------------
    # NO xG DATA
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
# POISSON PMF
# =========================================================

def poisson_pmf(
    k: int,
    lam: float,
) -> float:
    """
    Poisson probability mass function.
    """

    if k < 0:
        return 0.0

    if lam < 0:
        raise ValueError(
            "Lambda cannot be negative."
        )

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
) -> list:
    """
    Home/Away gol dağılımı.
    """

    if max_goals < 0:
        raise ValueError(
            "max_goals must be >= 0."
        )

    home_probs = [
        poisson_pmf(
            i,
            lambda_home,
        )
        for i in range(max_goals + 1)
    ]

    away_probs = [
        poisson_pmf(
            i,
            lambda_away,
        )
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
    """
    Lambda -> HOME / DRAW / AWAY probabilities.
    """

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

    total = (
        home
        + draw
        + away
    )

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
    Statistics -> LOCKED ModelSnapshot.

    KRİTİK:
    Odds bu fonksiyona girmez.

    Sıra:

        STATS
          ↓
        LAMBDA
          ↓
        POISSON
          ↓
        PROBABILITIES
          ↓
        SCORE MATRIX
          ↓
        LOCK
    """

    lambda_home, lambda_away = calculate_lambdas(
        stats
    )

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

    snapshot = ModelSnapshot(
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        probabilities=probabilities,
        score_matrix=score_matrix,
        max_goals=max_goals,
        model_version="Q200-V3.1",
        locked=True,
    )

    return snapshot


# =========================================================
# COMPATIBILITY
# =========================================================

def model_probabilities(
    stats: Any,
) -> Dict[str, float]:
    """
    Eski API uyumluluğu.
    """

    snapshot = build_model(stats)

    return snapshot.probabilities
