"""
Q200 Engine - Source Mapper

Q200 V3.1

External sources
        ↓
CanonicalMatchData

Supported sources:

1. StatsHub HOME
2. StatsHub AWAY
3. SoccerSTATS
4. PPI
5. Odds

CRITICAL RULES
--------------

- Lambda hesaplanmaz.
- Poisson hesaplanmaz.
- Monte Carlo çalıştırılmaz.
- Selection yapılmaz.
- Kelly hesaplanmaz.
- Odds model oluşturma aşamasında kullanılmaz.
- Eksik veri uydurulmaz.
- Kaynak izi korunur.
- Eski tek StatsHub API'si geriye dönük uyumludur.
"""

from __future__ import annotations

from typing import Any

from .models import (
    CanonicalMatchData,
    OddsData,
    PPIData,
    SoccerStatsData,
    StatsHubData,
)


SOURCE_MAPPER_VERSION = "Q200-SOURCE-MAPPER-V2"


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _put(
    values: dict[str, Any],
    trace: dict[str, str],
    key: str,
    value: Any,
    source: str,
) -> None:
    """
    Değer mevcutsa canonical sözlüğe ekler.

    None değerler hiçbir zaman eklenmez.
    """

    if value is None:
        return

    values[key] = value
    trace[key] = source


def _put_if_missing(
    values: dict[str, Any],
    trace: dict[str, str],
    warnings: list[str],
    key: str,
    value: Any,
    source: str,
    *,
    priority_name: str = "öncelikli kaynak",
) -> None:
    """
    Alan boşsa ekler.

    Alan zaten mevcutsa mevcut değer korunur ve
    yeni kaynağın değeri warning olarak kaydedilir.
    """

    if value is None:
        return

    if key not in values:
        values[key] = value
        trace[key] = source
        return

    warnings.append(
        f"{key}: {priority_name} değeri korunmuştur; "
        f"{source} değeri kullanılmadı."
    )


# ---------------------------------------------------------------------------
# Match identity
# ---------------------------------------------------------------------------


def _norm_team(value: str) -> str:
    """
    Takım isimlerini karşılaştırma için normalize eder.
    """

    return "".join(
        character
        for character in value.casefold()
        if character.isalnum()
    )


def _same_team(
    left: str,
    right: str,
) -> bool:
    return _norm_team(left) == _norm_team(right)


def _validate_match_pair(
    expected: Any,
    actual: Any,
    source: str,
) -> None:
    """
    İki kaynağın HOME/AWAY takım kimliğini kontrol eder.
    """

    if expected is None:
        raise ValueError(
            "Beklenen match bilgisi bulunamadı."
        )

    if actual is None:
        raise ValueError(
            f"{source} match bilgisi bulunamadı."
        )

    if not _same_team(
        expected.home_team,
        actual.home_team,
    ):
        raise ValueError(
            f"{source} HOME takımı eşleşmiyor: "
            f"{expected.home_team} != {actual.home_team}"
        )

    if not _same_team(
        expected.away_team,
        actual.away_team,
    ):
        raise ValueError(
            f"{source} AWAY takımı eşleşmiyor: "
            f"{expected.away_team} != {actual.away_team}"
        )


# ---------------------------------------------------------------------------
# SoccerSTATS
# ---------------------------------------------------------------------------


def map_soccerstats(
    data: SoccerStatsData,
) -> tuple[
    dict[str, Any],
    dict[str, str],
]:
    """
    SoccerStatsData → canonical fields.
    """

    if not isinstance(
        data,
        SoccerStatsData,
    ):
        raise TypeError(
            "data SoccerStatsData olmalıdır."
        )

    values: dict[str, Any] = {}
    trace: dict[str, str] = {}

    goals = data.goals
    corners = data.corners
    form = data.form
    h2h = data.h2h
    distribution = data.distribution
    timing = data.timing

    source = "SoccerSTATS"

    # Goals ---------------------------------------------------------------

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

    # Corners -------------------------------------------------------------

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
        "corners_over_7_5",
        corners.over_7_5,
        source,
    )

    _put(
        values,
        trace,
        "corners_over_8_5",
        corners.over_8_5,
        source,
    )

    _put(
        values,
        trace,
        "corners_over_9_5",
        corners.over_9_5,
        source,
    )

    _put(
        values,
        trace,
        "corners_over_10_5",
        corners.over_10_5,
        source,
    )

    _put(
        values,
        trace,
        "corners_over_11_5",
        corners.over_11_5,
        source,
    )

    _put(
        values,
        trace,
        "corners_over_12_5",
        corners.over_12_5,
        source,
    )

    _put(
        values,
        trace,
        "corners_over_13_5",
        corners.over_13_5,
        source,
    )

    # Form ----------------------------------------------------------------

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
        "home_points",
        form.home_points,
        source,
    )

    _put(
        values,
        trace,
        "away_points",
        form.away_points,
        source,
    )

    _put(
        values,
        trace,
        "home_matches",
        form.home_matches,
        source,
    )

    _put(
        values,
        trace,
        "away_matches",
        form.away_matches,
        source,
    )

    # H2H -----------------------------------------------------------------

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

    # Distribution --------------------------------------------------------

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

    # Timing --------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# StatsHub
# ---------------------------------------------------------------------------


def _map_statshub_team(
    *,
    data: StatsHubData,
    side: str,
    values: dict[str, Any],
    trace: dict[str, str],
    warnings: list[str],
) -> None:
    """
    Tek bir StatsHub HOME/AWAY kaynağını canonical alana aktarır.

    StatsHub OCR yapısı:

        goals_for
        goals_agt
        xg_for
        xg_agt
        ...

    HOME kaynağı:

        goals_for → home_gf_per_match
        goals_agt → home_ga_per_match
        xg_for    → home_xg
        xg_agt    → home_xga

    AWAY kaynağı:

        goals_for → away_gf_per_match
        goals_agt → away_ga_per_match
        xg_for    → away_xg
        xg_agt    → away_xga

    Bu dönüşüm açık ve deterministic'tir.
    Genel AVG değerleri takım değerine tahmin edilmez.
    """

    if not isinstance(
        data,
        StatsHubData,
    ):
        raise TypeError(
            "data StatsHubData olmalıdır."
        )

    if side not in {
        "home",
        "away",
    }:
        raise ValueError(
            "side yalnızca home veya away olabilir."
        )

    source_name = (
        "StatsHub HOME"
        if side == "home"
        else "StatsHub AWAY"
    )

    prefix = (
        "home"
        if side == "home"
        else "away"
    )

    # ------------------------------------------------------------------
    # Preserve every approved OCR value under a source-specific key.
    # ------------------------------------------------------------------

    for key, value in data.values.items():
        if value is None:
            continue

        namespaced_key = (
            f"statshub_{side}_{key}"
        )

        _put(
            values,
            trace,
            namespaced_key,
            value,
            source_name,
        )

    # ------------------------------------------------------------------
    # Explicit goal mapping.
    # ------------------------------------------------------------------

    goal_for = data.values.get(
        "goals_for"
    )

    goal_agt = data.values.get(
        "goals_agt"
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}_gf_per_match",
        goal_for,
        source_name,
        priority_name="öncelikli statistics kaynağı",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}_ga_per_match",
        goal_agt,
        source_name,
        priority_name="öncelikli statistics kaynağı",
    )

    # ------------------------------------------------------------------
    # Explicit xG mapping.
    # ------------------------------------------------------------------

    xg_for = data.values.get(
        "xg_for"
    )

    xg_agt = data.values.get(
        "xg_agt"
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}_xg",
        xg_for,
        source_name,
        priority_name="öncelikli statistics kaynağı",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}_xga",
        xg_agt,
        source_name,
        priority_name="öncelikli statistics kaynağı",
    )


def _map_legacy_statshub(
    data: StatsHubData,
    values: dict[str, Any],
    trace: dict[str, str],
    warnings: list[str],
) -> None:
    """
    Eski tek StatsHub girişini destekler.

    ÖNEMLİ:

    Genel AVG değerleri home/away tarafına tahmin edilmez.

    Yalnızca açıkça canonical isimlendirilmiş alanlar
    canonical modele aktarılır.
    """

    source = "StatsHub"

    for key, value in data.values.items():

        if value is None:
            continue

        if key not in values:
            values[key] = value
            trace[key] = source
            continue

        warnings.append(
            f"{key}: SoccerSTATS öncelikli; "
            "StatsHub değeri kullanılmadı."
        )


# ---------------------------------------------------------------------------
# PPI
# ---------------------------------------------------------------------------


def _map_ppi(
    data: PPIData,
    values: dict[str, Any],
    trace: dict[str, str],
) -> None:
    """
    PPI verisini canonical context alanlarına aktarır.

    PPI lambda hesabına otomatik ağırlık olarak sokulmaz.
    """

    source = "PPI"

    _put(
        values,
        trace,
        "ppi_home_ppg",
        data.home_ppg,
        source,
    )

    _put(
        values,
        trace,
        "ppi_away_ppg",
        data.away_ppg,
        source,
    )

    _put(
        values,
        trace,
        "ppi_home_ppi",
        data.home_ppi,
        source,
    )

    _put(
        values,
        trace,
        "ppi_away_ppi",
        data.away_ppi,
        source,
    )

    _put(
        values,
        trace,
        "ppi_home_opponent_ppg",
        data.home_opponent_ppg,
        source,
    )

    _put(
        values,
        trace,
        "ppi_away_opponent_ppg",
        data.away_opponent_ppg,
        source,
    )

    _put(
        values,
        trace,
        "ppi_home_rank",
        data.home_rank,
        source,
    )

    _put(
        values,
        trace,
        "ppi_away_rank",
        data.away_rank,
        source,
    )


# ---------------------------------------------------------------------------
# Five-source mapper
# ---------------------------------------------------------------------------


def map_five_sources(
    *,
    soccerstats: SoccerStatsData | None = None,
    statshub_home: StatsHubData | None = None,
    statshub_away: StatsHubData | None = None,
    ppi: PPIData | None = None,
    odds: OddsData | None = None,
) -> CanonicalMatchData:
    """
    Beş kaynaklı girişleri CanonicalMatchData'ya dönüştürür.

    Kaynaklar:

        StatsHub HOME
        StatsHub AWAY
        SoccerSTATS
        PPI
        Odds

    Statistics priority:

        1. SoccerSTATS
        2. StatsHub HOME/AWAY

    PPI:

        Context olarak saklanır.

    Odds:

        CanonicalMatchData içinde saklanır ancak
        canonical_values içine girmez.

        Böylece odds model oluşturma aşamasını etkileyemez.
    """

    if (
        soccerstats is None
        and statshub_home is None
        and statshub_away is None
        and ppi is None
        and odds is None
    ):
        raise ValueError(
            "En az bir source verilmelidir."
        )

    # ------------------------------------------------------------------
    # Determine match identity.
    # ------------------------------------------------------------------

    match = None

    if soccerstats is not None:
        match = soccerstats.match

    elif (
        statshub_home is not None
        and statshub_home.match is not None
    ):
        match = statshub_home.match

    elif (
        statshub_away is not None
        and statshub_away.match is not None
    ):
        match = statshub_away.match

    elif (
        ppi is not None
        and ppi.match is not None
    ):
        match = ppi.match

    elif (
        odds is not None
        and odds.match is not None
    ):
        match = odds.match

    if match is None:
        raise ValueError(
            "Canonical data için match bilgisi gereklidir."
        )

    # ------------------------------------------------------------------
    # Validate every source against match identity.
    # ------------------------------------------------------------------

    if soccerstats is not None:
        _validate_match_pair(
            match,
            soccerstats.match,
            "SoccerSTATS",
        )

    if statshub_home is not None:
        if statshub_home.match is not None:
            _validate_match_pair(
                match,
                statshub_home.match,
                "StatsHub HOME",
            )

    if statshub_away is not None:
        if statshub_away.match is not None:
            _validate_match_pair(
                match,
                statshub_away.match,
                "StatsHub AWAY",
            )

    if ppi is not None:
        if ppi.match is not None:
            _validate_match_pair(
                match,
                ppi.match,
                "PPI",
            )

    if odds is not None:
        if odds.match is not None:
            _validate_match_pair(
                match,
                odds.match,
                "Odds",
            )

    canonical_values: dict[str, Any] = {}
    source_trace: dict[str, str] = {}
    warnings: list[str] = []

    # ------------------------------------------------------------------
    # 1. SoccerSTATS — primary statistics source.
    # ------------------------------------------------------------------

    if soccerstats is not None:

        values, trace = map_soccerstats(
            soccerstats
        )

        canonical_values.update(
            values
        )

        source_trace.update(
            trace
        )

    # ------------------------------------------------------------------
    # 2. StatsHub HOME.
    # ------------------------------------------------------------------

    if statshub_home is not None:

        _map_statshub_team(
            data=statshub_home,
            side="home",
            values=canonical_values,
            trace=source_trace,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # 3. StatsHub AWAY.
    # ------------------------------------------------------------------

    if statshub_away is not None:

        _map_statshub_team(
            data=statshub_away,
            side="away",
            values=canonical_values,
            trace=source_trace,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # 4. PPI.
    # ------------------------------------------------------------------

    if ppi is not None:

        _map_ppi(
            data=ppi,
            values=canonical_values,
            trace=source_trace,
        )

    # ------------------------------------------------------------------
    # Return.
    # ------------------------------------------------------------------

    return CanonicalMatchData(
        match=match,
        soccerstats=soccerstats,
        statshub=(
            statshub_home
            if statshub_home is not None
            else statshub_away
        ),
        odds=odds,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        ppi=ppi,
        canonical_values=canonical_values,
        source_trace=source_trace,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Backward-compatible mapper
# ---------------------------------------------------------------------------


def map_sources(
    *,
    soccerstats: SoccerStatsData | None = None,
    statshub: StatsHubData | None = None,
    statshub_home: StatsHubData | None = None,
    statshub_away: StatsHubData | None = None,
    ppi: PPIData | None = None,
    odds: OddsData | None = None,
) -> CanonicalMatchData:
    """
    Geriyə dönük uyumlu source mapper.

    Eski kullanım:

        map_sources(
            soccerstats=...,
            statshub=...,
        )

    Yeni kullanım:

        map_sources(
            soccerstats=...,
            statshub_home=...,
            statshub_away=...,
            ppi=...,
            odds=...,
        )

    Eski tek StatsHub kaynağı:
        statshub

    ayrı bir home/away bilgisi taşımadığı için
    yalnızca açık canonical alanları doldurur.
    """

    if statshub is not None:

        if (
            statshub_home is not None
            or statshub_away is not None
        ):
            raise ValueError(
                "statshub ile statshub_home/statshub_away "
                "aynı anda kullanılamaz."
            )

        # Eski davranışı koruyoruz.
        result = map_five_sources(
            soccerstats=soccerstats,
            ppi=ppi,
            odds=odds,
        )

        values = dict(
            result.canonical_values
        )

        trace = dict(
            result.source_trace
        )

        warnings = list(
            result.warnings
        )

        _map_legacy_statshub(
            statshub,
            values,
            trace,
            warnings,
        )

        return CanonicalMatchData(
            match=result.match,
            soccerstats=result.soccerstats,
            statshub=statshub,
            odds=result.odds,
            statshub_home=None,
            statshub_away=None,
            ppi=result.ppi,
            canonical_values=values,
            source_trace=trace,
            warnings=warnings,
        )

    return map_five_sources(
        soccerstats=soccerstats,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        ppi=ppi,
        odds=odds,
    )


__all__ = [
    "SOURCE_MAPPER_VERSION",
    "map_soccerstats",
    "map_five_sources",
    "map_sources",
]
