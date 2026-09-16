from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TeamStats:
    """
    Q200 takım istatistikleri.

    Yeni şema:
        home_gf
        home_ga
        away_gf
        away_ga
        home_xg
        home_xga
        away_xg
        away_xga

    Eski 7-parametreli testlerle uyumluluk:
        TeamStats(
            home_gf,
            home_ga,
            away_gf,
            away_ga,
            home_xg,
            home_xga,
            away_xga
        )

    Yani 7. positional değer AWAY xGA olarak kabul edilir.
    """

    home_gf: float = 0.0
    home_ga: float = 0.0

    away_gf: float = 0.0
    away_ga: float = 0.0

    home_xg: Optional[float] = None
    home_xga: Optional[float] = None

    # Eski testlerle uyumluluk için:
    away_xga: Optional[float] = None

    # Yeni API için AWAY xG
    away_xg: Optional[float] = None


@dataclass(frozen=True)
class ModelSnapshot:
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


@dataclass(frozen=True)
class OddsInput:
    market: str
    odds: Dict[str, float]


@dataclass
class AnalysisResult:
    snapshot: ModelSnapshot
    fair_odds: Dict[str, float]
    no_vig_probabilities: Dict[str, float]
    ev: Dict[str, float]
    selections: list
