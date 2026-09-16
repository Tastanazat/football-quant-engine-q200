from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class TeamStats:
    """
    Q200 takım istatistikleri.

    İlk dört değer temel GF/GA verileridir.
    xG alanları opsiyoneldir.
    """

    home_gf: float
    home_ga: float
    away_gf: float
    away_ga: float = 0.0

    home_xg: Optional[float] = None
    home_xga: Optional[float] = None
    away_xg: Optional[float] = None
    away_xga: Optional[float] = None


@dataclass(frozen=True)
class ModelSnapshot:
    """
    LOCK edilmiş Q200 model çıktısı.
    """

    lambda_home: float
    lambda_away: float
    probabilities: Dict[str, float]
    max_goals: int
    model_version: str
    locked: bool = True

    @property
    def model_locked(self) -> bool:
        return self.locked


@dataclass(frozen=True)
class OddsInput:
    """
    Odds katmanı.

    Model oluşturulurken kullanılmaz.
    """

    market: str
    odds: Dict[str, float]


@dataclass
class AnalysisResult:
    """
    Q200 analiz sonucu.
    """

    snapshot: ModelSnapshot
    fair_odds: Dict[str, float]
    no_vig_probabilities: Dict[str, float]
    ev: Dict[str, float]
    selections: List[dict] = field(default_factory=list)
