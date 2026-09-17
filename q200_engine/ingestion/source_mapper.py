"""
Q200 Engine - Source Mapper

Q200 V3.1

External source data
        ↓
CanonicalMatchData

Bu katman:
- Kaynak alanlarını canonical alanlara dönüştürür.
- Kaynak bilgisini korur.
- Eksik veriyi uydurmaz.
- Odds'u model verisine karıştırmaz.

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Selection yapmaz.
- Kelly hesaplamaz.
"""

from __future__ import annotations

from typing import Any

from .models import (
    CanonicalMatchData,
    SoccerStatsData,
    StatsHubData,
)


SOURCE_MAPPER_VERSION = "Q200-SOURCE-MAPPER-V1"


def _put(
    values: dict[str, Any],
    trace: dict[str, str],
    key: str,
    value: Any,
    source: str,
) -> None:
    """
    Değer mevcutsa canonical sözlüğe ekler.

    None değerleri eklemeyerek eksik veriyi açıkça
    eksik bırakırız.
    """

    if value is None:
        return

    values[key] = value
    trace[key] = source


def map_soccerstats(
    data: SoccerStatsData,
) -> tuple[dict[str, Any], dict[str, str]]:
    """
    SoccerStatsData → canonical fields.
    """

    values: dict[str, Any] = {}
    trace: dict[str, str] = {}

    goals = data.goals
    corners = data.corners
    form = data.form
    h2h = data.h2h
    distribution = data.distribution
    timing = data.timing

    source = "SoccerSTATS"

    _put(
        values,
        trace,
        "home_gf",
        goals.home_gf,
        source,
    )

    _put(
        values,
        trace,
        "home_ga",
        goals.home_ga,
        source,
    )

    _put(
        values,
        trace,
        "away_gf",
        goals.away_gf,
        source,
    )

    _put(
        values,
        trace,
        "away_ga",
        goals.away_ga,
        source,
    )

    _put(
        values,
        trace,
        "home_gf_per_match",
        goals.home_gf_per_match,
        source,
    )

    _put(
        values,
        trace,
        "home_ga_per_match",
        goals.home_ga_per_match,
        source,
    )

    _put(
        values,
        trace,
        "away_gf_per_match",
        goals.away_gf_per_match,
        source,
    )

    _put(
        values,
        trace,
        "away_ga_per_match",
        goals.away_ga_per_match,
        source,
    )

    _put(
        values,
        trace,
        "home_scoring_rate",
        goals.home_scoring_rate,
        source,
    )

    _put(
        values,
        trace,
        "away_scoring_rate",
        goals.away_scoring_rate,
        source,
    )

    _put(
        values,
        trace,
        "home_conceding_rate",
        goals.home_conceding_rate,
        source,
    )

    _put(
        values,
        trace,
        "away_conceding_rate",
        goals.away_conceding_rate,
        source,
    )

    _put(
        values,
        trace,
        "over_1_5",
        goals.over_1_5,
        source,
    )

    _put(
        values,
        trace,
        "over_2_5",
        goals.over_2_5,
        source,
    )

    _put(
        values,
        trace,
        "over_3_5",
        goals.over_3_5,
        source,
    )

    _put(
        values,
        trace,
        "btts",
        goals.btts,
        source,
    )

    _put(
        values,
        trace,
        "home_corners_for",
        corners.home_corners_for,
        source,
    )

    _put(
        values,
        trace,
        "home_corners_against",
        corners.home_corners_against,
        source,
    )

    _put(
        values,
        trace,
        "away_corners_for",
        corners.away_corners_for,
        source,
    )

    _put(
        values,
        trace,
        "away_corners_against",
        corners.away_corners_against,
        source,
    )

    _put(
        values,
        trace,
        "home_total_corners",
        corners.home_total_corners,
        source,
    )

    _put(
        values,
        trace,
        "away_total_corners",
        corners.away_total_corners,
        source,
    )

    _put(
        values,
        trace,
        "home_ppg",
        form.home_ppg,
        source,
    )

    _put(
        values,
        trace,
        "away_ppg",
        form.away_ppg,
        source,
    )

    _put(
        values,
        trace,
        "h2h_matches",
        h2h.matches,
        source,
    )

    _put(
        values,
        trace,
        "h2h_home_wins",
        h2h.home_wins,
        source,
    )

    _put(
        values,
        trace,
        "h2h_draws",
        h2h.draws,
        source,
    )

    _put(
        values,
        trace,
        "h2h_away_wins",
        h2h.away_wins,
        source,
    )

    _put(
        values,
        trace,
        "h2h_home_goals",
        h2h.home_goals,
        source,
    )

    _put(
        values,
        trace,
        "h2h_away_goals",
        h2h.away_goals,
        source,
    )

    _put(
        values,
        trace,
        "h2h_home_goals_per_match",
        h2h.home_goals_per_match,
        source,
    )

    _put(
        values,
        trace,
        "h2h_away_goals_per_match",
        h2h.away_goals_per_match,
        source,
    )

    _put(
        values,
        trace,
        "h2h_total_goals_per_match",
        h2h.total_goals_per_match,
        source,
    )

    _put(
        values,
        trace,
        "h2h_home_scored_rate",
        h2h.home_scored_rate,
        source,
    )

    _put(
        values,
        trace,
        "h2h_away_scored_rate",
        h2h.away_scored_rate,
        source,
    )

    _put(
        values,
        trace,
        "h2h_btts_rate",
        h2h.btts_rate,
        source,
    )

    _put(
        values,
        trace,
        "h2h_over_1_5",
        h2h.over_1_5,
        source,
    )

    _put(
        values,
        trace,
        "h2h_over_2_5",
        h2h.over_2_5,
        source,
    )

    _put(
        values,
        trace,
        "h2h_over_3_5",
        h2h.over_3_5,
        source,
    )

    _put(
        values,
        trace,
        "home_points_percentage",
        distribution.home_points_percentage,
        source,
    )

    _put(
        values,
        trace,
        "away_points_percentage",
        distribution.away_points_percentage,
        source,
    )

    _put(
        values,
        trace,
        "home_goals_percentage",
        distribution.home_goals_percentage,
        source,
    )

    _put(
        values,
        trace,
        "away_goals_percentage",
        distribution.away_goals_percentage,
        source,
    )

    _put(
        values,
        trace,
        "home_goals_conceded_percentage",
        distribution.home_goals_conceded_percentage,
        source,
    )

    _put(
        values,
        trace,
        "away_goals_conceded_percentage",
        distribution.away_goals_conceded_percentage,
        source,
    )

    _put(
        values,
        trace,
        "home_average_goal_minute_for",
        timing.home_average_goal_minute_for,
        source,
    )

    _put(
        values,
        trace,
        "away_average_goal_minute_for",
        timing.away_average_goal_minute_for,
        source,
    )

    _put(
        values,
        trace,
        "home_average_goal_minute_against",
        timing.home_average_goal_minute_against,
        source,
    )

    _put(
        values,
        trace,
        "away_average_goal_minute_against",
        timing.away_average_goal_minute_against,
        source,
    )

    return values, trace


def map_sources(
    *,
    soccerstats: SoccerStatsData | None = None,
    statshub: StatsHubData | None = None,
) -> CanonicalMatchData:
    """
    External kaynakları CanonicalMatchData'ya dönüştürür.

    Öncelik:
        1. SoccerSTATS
        2. StatsHub

    Ancak yalnızca gerçekten mevcut olan değerler kullanılır.

    Odds burada özellikle işlenmez.
    """

    if soccerstats is None and statshub is None:
        raise ValueError(
            "En az bir statistics source verilmelidir."
        )

    match = (
        soccerstats.match
        if soccerstats is not None
        else statshub.match
    )

    if match is None:
        raise ValueError(
            "Canonical data için match bilgisi gereklidir."
        )

    canonical_values: dict[str, Any] = {}
    source_trace: dict[str, str] = {}
    warnings: list[str] = []

    if soccerstats is not None:
        values, trace = map_soccerstats(
            soccerstats
        )

        canonical_values.update(values)
        source_trace.update(trace)

    if statshub is not None:
        for key, value in statshub.values.items():

            if value is None:
                continue

            if key not in canonical_values:
                canonical_values[key] = value
                source_trace[key] = "StatsHub"

            else:
                warnings.append(
                    f"{key}: SoccerSTATS öncelikli; "
                    "StatsHub değeri kullanılmadı."
                )

    if soccerstats is None and statshub is not None:
        source_trace = {
            key: "StatsHub"
            for key in canonical_values
        }

    return CanonicalMatchData(
        match=match,
        soccerstats=soccerstats,
        statshub=statshub,
        canonical_values=canonical_values,
        source_trace=source_trace,
        warnings=warnings,
    )


__all__ = [
    "SOURCE_MAPPER_VERSION",
    "map_soccerstats",
    "map_sources",
]
