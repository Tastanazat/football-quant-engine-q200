"""
Q200 Engine - Schema Layer

Veri modelleri ve tip tanımları.

Q200 V3.1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =========================================================
# TEAM STATS
# =========================================================

@dataclass(frozen=True)
class TeamStats:
    """
    Q200 takım istatistikleri.

    Alan sırası:

        1. home_gf
        2. home_ga
        3. away_gf
        4. away_ga
        5. home_xg
        6. home_xga
        7. away_xga
        8. away_xg
    """

    home_gf: float
    home_ga: float
    away_gf: float

    away_ga: float = 0.0

    home_xg: Optional[float] = None
    home_xga: Optional[float] = None

    # Legacy alan
    away_xga: Optional[float] = None

    # Yeni standart alan
    away_xg: Optional[float] = None


# =========================================================
# MODEL SNAPSHOT
# =========================================================

@dataclass(frozen=True)
class ModelSnapshot:
    """
    LOCK edilmiş model çıktısı.

    Odds katmanı bu nesneyi değiştiremez.
    """

    # -----------------------------------------------------
    # Lambda
    # -----------------------------------------------------

    lambda_home: float
    lambda_away: float

    # -----------------------------------------------------
    # Poisson model probabilities
    # -----------------------------------------------------

    probabilities: Dict[str, float]

    # -----------------------------------------------------
    # Score matrix
    # -----------------------------------------------------

    score_matrix: list

    # -----------------------------------------------------
    # Monte Carlo probabilities
    # -----------------------------------------------------

    monte_carlo_probabilities: Dict[str, float] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # Model configuration
    # -----------------------------------------------------

    max_goals: int = 10

    model_version: str = "Q200-V3.1"

    # -----------------------------------------------------
    # LOCK
    # -----------------------------------------------------

    locked: bool = True

    # -----------------------------------------------------
    # Compatibility property
    # -----------------------------------------------------

    @property
    def model_locked(self) -> bool:
        return self.locked


# =========================================================
# ODDS INPUT
# =========================================================

@dataclass(frozen=True)
class OddsInput:
    """
    Odds katmanı.

    Model katmanından tamamen bağımsızdır.
    """

    market: str

    odds: Dict[str, float]


# =========================================================
# ANALYSIS RESULT
# =========================================================

@dataclass
class AnalysisResult:
    """
    Pipeline nihai analiz sonucu.

    İçerik:

        Locked Model
        Fair Odds
        No-Vig
        Baseline EV
        Stress Probabilities
        Pessimistic Probabilities
        Pessimistic EV
        Final Selections
    """

    # -----------------------------------------------------
    # LOCKED MODEL
    # -----------------------------------------------------

    snapshot: ModelSnapshot

    # -----------------------------------------------------
    # FAIR ODDS
    # -----------------------------------------------------

    fair_odds: Dict[str, float] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # NO-VIG PROBABILITIES
    # -----------------------------------------------------

    no_vig_probabilities: Dict[str, float] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # BASELINE EXPECTED VALUE
    # -----------------------------------------------------

    ev: Dict[str, float] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # STRESS LAMBDAS
    # -----------------------------------------------------

    stress_lambdas: Dict[str, Dict[str, float]] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # STRESS MARKET PROBABILITIES
    # -----------------------------------------------------

    stress_probabilities: Dict[str, Dict[str, float]] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # PESSIMISTIC PROBABILITIES
    # -----------------------------------------------------

    pessimistic_probabilities: Dict[str, float] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # PESSIMISTIC EXPECTED VALUE
    # -----------------------------------------------------

    pessimistic_ev: Dict[str, float] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # FINAL SELECTIONS
    # -----------------------------------------------------

    selections: List[dict] = field(
        default_factory=list
    )
