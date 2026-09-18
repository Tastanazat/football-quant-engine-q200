"""
Q200 Engine - Ingestion Models

Q200 V3.1

External data sources:
    1. StatsHub HOME
    2. StatsHub AWAY
    3. SoccerSTATS
    4. PPI
    5. Odds

Bu katman yalnızca veriyi taşır.
Model, lambda, odds veya selection hesabı yapmaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


INGESTION_VERSION = "Q200-INGESTION-V2"


@dataclass(frozen=True)
class MatchInfo:
    """Maçın temel kimlik ve zaman bilgileri."""

    home_team: str
    away_team: str
    date: Optional[str] = None
    time: Optional[str] = None
    competition: Optional[str] = None
    source: Optional[str] = None


@dataclass(frozen=True)
class GoalStats:
    """Gol istatistikleri."""

    home_gf: Optional[float] = None
    home_ga: Optional[float] = None
    away_gf: Optional[float] = None
    away_ga: Optional[float] = None

    home_gf_per_match: Optional[float] = None
    home_ga_per_match: Optional[float] = None
    away_gf_per_match: Optional[float] = None
    away_ga_per_match: Optional[float] = None

    home_scoring_rate: Optional[float] = None
    away_scoring_rate: Optional[float] = None
    home_conceding_rate: Optional[float] = None
    away_conceding_rate: Optional[float] = None

    over_1_5: Optional[float] = None
    over_2_5: Optional[float] = None
    over_3_5: Optional[float] = None
    btts: Optional[float] = None


@dataclass(frozen=True)
class CornerStats:
    """Korner istatistikleri."""

    home_corners_for: Optional[float] = None
    home_corners_against: Optional[float] = None
    away_corners_for: Optional[float] = None
    away_corners_against: Optional[float] = None

    home_total_corners: Optional[float] = None
    away_total_corners: Optional[float] = None

    over_7_5: Optional[float] = None
    over_8_5: Optional[float] = None
    over_9_5: Optional[float] = None
    over_10_5: Optional[float] = None
    over_11_5: Optional[float] = None
    over_12_5: Optional[float] = None
    over_13_5: Optional[float] = None


@dataclass(frozen=True)
class FormStats:
    """Form ve performans istatistikleri."""

    home_ppg: Optional[float] = None
    away_ppg: Optional[float] = None

    home_points: Optional[float] = None
    away_points: Optional[float] = None

    home_matches: Optional[int] = None
    away_matches: Optional[int] = None


@dataclass(frozen=True)
class H2HStats:
    """Head-to-head istatistikleri."""

    matches: Optional[int] = None
    home_wins: Optional[int] = None
    draws: Optional[int] = None
    away_wins: Optional[int] = None

    home_goals: Optional[float] = None
    away_goals: Optional[float] = None

    home_goals_per_match: Optional[float] = None
    away_goals_per_match: Optional[float] = None

    total_goals_per_match: Optional[float] = None

    home_scored_rate: Optional[float] = None
    away_scored_rate: Optional[float] = None
    btts_rate: Optional[float] = None

    over_1_5: Optional[float] = None
    over_2_5: Optional[float] = None
    over_3_5: Optional[float] = None


@dataclass(frozen=True)
class TeamDistributionStats:
    """Takımın home/away dağılım bilgileri."""

    home_points_percentage: Optional[float] = None
    away_points_percentage: Optional[float] = None

    home_goals_percentage: Optional[float] = None
    away_goals_percentage: Optional[float] = None

    home_goals_conceded_percentage: Optional[float] = None
    away_goals_conceded_percentage: Optional[float] = None


@dataclass(frozen=True)
class TimingStats:
    """Gol zamanlaması istatistikleri."""

    home_average_goal_minute_for: Optional[float] = None
    away_average_goal_minute_for: Optional[float] = None

    home_average_goal_minute_against: Optional[float] = None
    away_average_goal_minute_against: Optional[float] = None

    goal_difference: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceData:
    """
    Tek bir kaynaktan gelen ham/canonical veri.

    values:
        Kaynağın çıkardığı alanlar.

    raw_text:
        PDF/OCR gibi kaynaklardan gelen ham metin.

    metadata:
        Sayfa, kaynak adı, parser bilgisi vb.
    """

    source: str
    values: Dict[str, Any] = field(default_factory=dict)
    raw_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SoccerStatsData:
    """
    SoccerSTATS PDF'sinden çıkarılan canonical veri.

    Bu yapı model hesabı yapmaz.
    """

    match: MatchInfo
    goals: GoalStats = field(default_factory=GoalStats)
    corners: CornerStats = field(default_factory=CornerStats)
    form: FormStats = field(default_factory=FormStats)
    h2h: H2HStats = field(default_factory=H2HStats)
    distribution: TeamDistributionStats = field(
        default_factory=TeamDistributionStats
    )
    timing: TimingStats = field(default_factory=TimingStats)

    raw_sections: Dict[str, Any] = field(default_factory=dict)
    source_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StatsHubData:
    """
    StatsHub OCR/parser sonucunun canonical taşıyıcısı.

    OCR'dan gelen değerler burada saklanır.
    Manuel düzeltme bu katmanda yapılmaz.
    """

    match: Optional[MatchInfo] = None
    values: Dict[str, Any] = field(default_factory=dict)
    raw_text: Optional[str] = None
    source_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PPIData:
    """
    Points Performance Index verisi.

    PPI modelin lambda hesabını doğrudan değiştirmez.
    Bu katman yalnızca veriyi taşır.

    Daha sonraki aşamada:
        PPI -> feature -> calibration/backtest
    katkısı ayrı olarak ölçülebilir.
    """

    match: Optional[MatchInfo] = None

    home_ppg: Optional[float] = None
    away_ppg: Optional[float] = None

    home_ppi: Optional[float] = None
    away_ppi: Optional[float] = None

    home_opponent_ppg: Optional[float] = None
    away_opponent_ppg: Optional[float] = None

    home_rank: Optional[int] = None
    away_rank: Optional[int] = None

    raw_text: Optional[str] = None
    source_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OddsData:
    """
    Odds kaynağından gelen veriler.

    ÖNEMLİ:
    Bu yapı model/lambda hesabına girmez.

    Odds yalnızca:
        MODEL LOCK
    sonrasında kullanılacaktır.
    """

    match: Optional[MatchInfo] = None
    markets: Dict[str, Dict[str, float]] = field(default_factory=dict)
    raw_text: Optional[str] = None
    source_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FiveSourceMatchInput:
    """
    Q200 V3.1 beş kaynaklı analiz girdisi.

    Kaynaklar:

        1. StatsHub HOME
        2. StatsHub AWAY
        3. SoccerSTATS
        4. PPI
        5. Odds

    Bu sınıf yalnızca veri taşıma sözleşmesidir.

    Burada:
        - lambda hesaplanmaz
        - probability hesaplanmaz
        - odds model içine sokulmaz
        - EV hesaplanmaz
        - Kelly hesaplanmaz
        - selection yapılmaz
    """

    match: MatchInfo

    statshub_home: Optional[StatsHubData] = None
    statshub_away: Optional[StatsHubData] = None

    soccerstats: Optional[SoccerStatsData] = None
    ppi: Optional[PPIData] = None
    odds: Optional[OddsData] = None

    source_metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        """Mevcut kaynak sayısını döndürür."""

        sources = (
            self.statshub_home,
            self.statshub_away,
            self.soccerstats,
            self.ppi,
            self.odds,
        )

        return sum(source is not None for source in sources)

    @property
    def statistics_source_count(self) -> int:
        """Mevcut istatistik kaynaklarının sayısını döndürür."""

        sources = (
            self.statshub_home,
            self.statshub_away,
            self.soccerstats,
            self.ppi,
        )

        return sum(source is not None for source in sources)

    @property
    def has_odds(self) -> bool:
        """Odds kaynağının mevcut olup olmadığını döndürür."""

        return self.odds is not None


@dataclass(frozen=True)
class CanonicalMatchData:
    """
    Tüm external kaynakların birleştiği canonical veri.

    Source priority daha sonraki mapping katmanında uygulanır.
    Bu sınıf yalnızca veriyi taşır.

    Geriye dönük uyumluluk amacıyla eski:
        statshub
        soccerstats
        odds

    alanları korunmuştur.

    Yeni 5 kaynaklı pipeline ise:
        statshub_home
        statshub_away
        soccerstats
        ppi
        odds

    alanlarını kullanabilir.
    """

    match: MatchInfo

    soccerstats: Optional[SoccerStatsData] = None
    statshub: Optional[StatsHubData] = None
    odds: Optional[OddsData] = None

    statshub_home: Optional[StatsHubData] = None
    statshub_away: Optional[StatsHubData] = None
    ppi: Optional[PPIData] = None

    canonical_values: Dict[str, Any] = field(default_factory=dict)

    source_trace: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def model_to_dict(value: Any) -> Any:
    """
    Dataclass yapılarını recursive olarak JSON uyumlu
    dict/list yapısına dönüştürür.
    """

    if hasattr(value, "__dataclass_fields__"):
        result: Dict[str, Any] = {}

        for name in value.__dataclass_fields__:
            result[name] = model_to_dict(getattr(value, name))

        return result

    if isinstance(value, dict):
        return {
            str(key): model_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [model_to_dict(item) for item in value]

    return value


__all__ = [
    "INGESTION_VERSION",
    "MatchInfo",
    "GoalStats",
    "CornerStats",
    "FormStats",
    "H2HStats",
    "TeamDistributionStats",
    "TimingStats",
    "SourceData",
    "SoccerStatsData",
    "StatsHubData",
    "PPIData",
    "OddsData",
    "FiveSourceMatchInput",
    "CanonicalMatchData",
    "model_to_dict",
]
