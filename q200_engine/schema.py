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

    7 parametre:
        TeamStats(
            home_gf,
            home_ga,
            away_gf,
            away_ga,
            home_xg,
            home_xga,
            away_xga,
        )

    8 parametre:
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

    # Legacy 7. alan
    away_xga: Optional[float] = None

    # Yeni 8. alan
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

    lambda_home: float
    lambda_away: float

    probabilities: Dict[str, float]

    score_matrix: list

    max_goals: int = 10

    model_version: str = "Q200-V3.1"

    locked: bool = True

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

    Model katmanından bağımsızdır.
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
    """

    snapshot: ModelSnapshot

    fair_odds: Dict[str, float] = field(
        default_factory=dict
    )

    no_vig_probabilities: Dict[str, float] = field(
        default_factory=dict
    )

    ev: Dict[str, float] = field(
        default_factory=dict
    )

    selections: List[dict] = field(
        default_factory=list
    )
