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

    İlk 3 alan zorunludur.

    Legacy kullanım:

        TeamStats(2, 1, 1)

    7 parametreli kullanım:

        TeamStats(
            home_gf,
            home_ga,
            away_gf,
            away_ga,
            home_xg,
            home_xga,
            away_xga,
        )

    8 parametreli kullanım:

        TeamStats(
            home_gf,
            home_ga,
            away_gf,
            away_ga,
            home_xg,
            home_xga,
            away_xga,
            away_xg,
        )
    """

    home_gf: float
    home_ga: float
    away_gf: float

    away_ga: float = 0.0

    home_xg: Optional[float] = None
    home_xga: Optional[float] = None

    # -----------------------------------------------------
    # Legacy alan
    # -----------------------------------------------------

    away_xga: Optional[float] = None

    # -----------------------------------------------------
    # Yeni standart alan
    # -----------------------------------------------------

    away_xg: Optional[float] = None


# =========================================================
# MODEL SNAPSHOT
# =========================================================

@dataclass(frozen=True)
class ModelSnapshot:
    """
    LOCK edilmiş model çıktısı.

    Bu nesne MODEL aşamasının sonucudur.

    Odds katmanı bu nesneyi değiştiremez.

    İçerik:

        lambda_home
        lambda_away
        model probabilities
        score matrix
        Monte Carlo probabilities
        model version
        lock status
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
        """
        Modelin LOCK durumunu döndürür.
        """

        return self.locked


# =========================================================
# ODDS INPUT
# =========================================================

@dataclass(frozen=True)
class OddsInput:
    """
    Odds katmanı.

    Model katmanından tamamen bağımsızdır.

    Odds bilgisi ModelSnapshot oluşturulurken
    kullanılmaz.
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

    ModelSnapshot LOCK edilmiş model çıktısını taşır.

    Odds aşamasından sonra:

        Fair Odds
        No-Vig
        EV
        Selections

    burada tutulur.
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
    # EXPECTED VALUE
    # -----------------------------------------------------

    ev: Dict[str, float] = field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # FINAL SELECTIONS
    # -----------------------------------------------------

    selections: List[dict] = field(
        default_factory=list
    )
