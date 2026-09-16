from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class TeamStats:
    home_gf: float
    home_ga: float
    away_gf: float
    away_ga: float
    home_xg: Optional[float] = None
    home_xga: Optional[float] = None
    away_xg: Optional[float] = None
    away_xga: Optional[float] = None


@dataclass(frozen=True)
class ModelSnapshot:
    lambda_home: float
    lambda_away: float
    probabilities: Dict[str, float]
    max_goals: int
    model_version: str
    locked: bool = True


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
    selections: list = field(default_factory=list)
