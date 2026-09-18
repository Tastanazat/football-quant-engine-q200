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


SOURCE_MAPPER_VERSION = "Q200-SOURCE-MAPPER-V1"


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
        "total_goals_avg",
        goals.total_goals_avg,
        source,
    )

    _put(
        values,
        trace,
        "over_15_pct",
        goals.over_15_pct,
        source,
    )

    _put(
        values,
        trace,
        "over_25_pct",
        goals.over_25_pct,
        source,
    )

    _put(
        values,
        trace,
        "over_35_pct",
        goals.over_35_pct,
        source,
    )

    _put(
        values,
        trace,
        "btts_pct",
        goals.btts_pct,
        source,
    )

    # Corners -------------------------------------------------------------

    _put(
        values,
        trace,
        "home_corners_avg",
        corners.home_avg,
        source,
    )

    _put(
        values,
        trace,
        "away_corners_avg",
        corners.away_avg,
        source,
    )

    _put(
        values,
        trace,
        "total_corners_avg",
        corners.total_avg,
        source,
    )

    # Form ----------------------------------------------------------------

    _put(
        values,
        trace,
        "home_form_points",
        form.home_points,
        source,
    )

    _put(
        values,
        trace,
        "away_form_points",
        form.away_points,
        source,
    )

    _put(
        values,
        trace,
        "home_form_goals_for",
        form.home_goals_for,
        source,
    )

    _put(
        values,
        trace,
        "home_form_goals_against",
        form.home_goals_against,
        source,
    )

    _put(
        values,
        trace,
        "away_form_goals_for",
        form.away_goals_for,
        source,
    )

    _put(
        values,
        trace,
        "away_form_goals_against",
        form.away_goals_against,
        source,
    )

    # H2H -----------------------------------------------------------------

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
        "h2h_over_25_pct",
        h2h.over_25_pct,
        source,
    )

    _put(
        values,
        trace,
        "h2h_btts_pct",
        h2h.btts_pct,
        source,
    )

    # Distribution --------------------------------------------------------

    _put(
        values,
        trace,
        "home_clean_sheet_pct",
        distribution.home_clean_sheet_pct,
        source,
    )

    _put(
        values,
        trace,
        "away_clean_sheet_pct",
        distribution.away_clean_sheet_pct,
        source,
    )

    _put(
        values,
        trace,
        "home_failed_to_score_pct",
        distribution.home_failed_to_score_pct,
        source,
    )

    _put(
        values,
        trace,
        "away_failed_to_score_pct",
        distribution.away_failed_to_score_pct,
        source,
    )

    # Timing --------------------------------------------------------------

    _put(
        values,
        trace,
        "goal_0_15_pct",
        timing.goal_0_15_pct,
        source,
    )

    _put(
        values,
        trace,
        "goal_16_30_pct",
        timing.goal_16_30_pct,
        source,
    )

    _put(
        values,
        trace,
        "goal_31_45_pct",
        timing.goal_31_45_pct,
        source,
    )

    _put(
        values,
        trace,
        "goal_46_60_pct",
        timing.goal_46_60_pct,
        source,
    )

    _put(
        values,
        trace,
        "goal_61_75_pct",
        timing.goal_61_75_pct,
        source,
    )

    _put(
        values,
        trace,
        "goal_76_90_pct",
        timing.goal_76_90_pct,
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
    StatsHub takım verisini canonical alanlara map eder.

    side:
        home
        away
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
            "side 'home' veya 'away' olmalıdır."
        )

    source = (
        "StatsHub HOME"
        if side == "home"
        else "StatsHub AWAY"
    )

    prefix = f"{side}_"

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}gf",
        data.gf,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}ga",
        data.ga,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}gf_per_match",
        data.gf_per_match,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}ga_per_match",
        data.ga_per_match,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}corners_avg",
        data.corners_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}shots_on_target_avg",
        data.shots_on_target_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}shots_in_box_avg",
        data.shots_in_box_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}total_shots_avg",
        data.total_shots_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}possession_avg",
        data.possession_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}passes_avg",
        data.passes_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}touches_opp_box_avg",
        data.touches_opp_box_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}big_chance_created_avg",
        data.big_chance_created_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}big_chance_scored_avg",
        data.big_chance_scored_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}big_chance_missed_avg",
        data.big_chance_missed_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}xg",
        data.xg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}xga",
        data.xga,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}cards_avg",
        data.cards_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}fouls_avg",
        data.fouls_avg,
        source,
        priority_name="SoccerSTATS",
    )

    _put_if_missing(
        values,
        trace,
        warnings,
        f"{prefix}offsides_avg",
        data.offsides_avg,
        source,
        priority_name="SoccerSTATS",
    )


def _map_legacy_statshub(
    data: StatsHubData,
    values: dict[str, Any],
    trace: dict[str, str],
    warnings: list[str],
) -> None:
    """
    Eski tek StatsHub API'sini canonical alanlara map eder.

    ÖNEMLİ:

    Genel StatsHub AVG değerlerinden HOME/AWAY takım
    değerleri tahmin edilmez.

    Örneğin:

        Goals AVG = 3.05

    değerinden:

        home_gf = 1.525
        away_gf = 1.525

    gibi yapay bir dağılım oluşturulmaz.

    Yalnızca açıkça takım bazında bulunan alanlar kullanılır.
    """

    if not isinstance(
        data,
        StatsHubData,
    ):
        raise TypeError(
            "data StatsHubData olmalıdır."
        )

    source = "StatsHub"

    # Legacy source fields are only accepted when they are
    # explicitly represented by the data model.

    _put(
        values,
        trace,
        "statshub_gf",
        data.gf,
        source,
    )

    _put(
        values,
        trace,
        "statshub_ga",
        data.ga,
        source,
    )

    _put(
        values,
        trace,
        "statshub_gf_per_match",
        data.gf_per_match,
        source,
    )

    _put(
        values,
        trace,
        "statshub_ga_per_match",
        data.ga_per_match,
        source,
    )

    _put(
        values,
        trace,
        "statshub_corners_avg",
        data.corners_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_shots_on_target_avg",
        data.shots_on_target_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_shots_in_box_avg",
        data.shots_in_box_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_total_shots_avg",
        data.total_shots_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_possession_avg",
        data.possession_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_passes_avg",
        data.passes_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_touches_opp_box_avg",
        data.touches_opp_box_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_big_chance_created_avg",
        data.big_chance_created_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_big_chance_scored_avg",
        data.big_chance_scored_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_big_chance_missed_avg",
        data.big_chance_missed_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_xg",
        data.xg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_xga",
        data.xga,
        source,
    )

    _put(
        values,
        trace,
        "statshub_cards_avg",
        data.cards_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_fouls_avg",
        data.fouls_avg,
        source,
    )

    _put(
        values,
        trace,
        "statshub_offsides_avg",
        data.offsides_avg,
        source,
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
    PPI verisini canonical context alanlarına map eder.
    """

    if not isinstance(
        data,
        PPIData,
    ):
        raise TypeError(
            "data PPIData olmalıdır."
        )

    source = "PPI"

    _put(
        values,
        trace,
        "ppi_home_ppg",
        data.home_ppi,
        source,
    )

    _put(
        values,
        trace,
        "ppi_away_ppg",
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

        # Eski tek StatsHub API'si için doğrudan legacy path kullanılır.
        # Böylece yalnızca StatsHub verisiyle çalışan mevcut pipeline ve
        # testler korunur; map_five_sources()'un five-source guard'ına
        # yanlışlıkla girilmez.
        match = statshub.match

        if match is None:
            raise ValueError(
                "StatsHub match bilgisi gereklidir."
            )

        if soccerstats is not None:
            _validate_match_pair(
                match,
                soccerstats.match,
                "SoccerSTATS",
            )

        if ppi is not None and ppi.match is not None:
            _validate_match_pair(
                match,
                ppi.match,
                "PPI",
            )

        if odds is not None and odds.match is not None:
            _validate_match_pair(
                match,
                odds.match,
                "Odds",
            )

        values: dict[str, Any] = {}
        trace: dict[str, str] = {}
        warnings: list[str] = []

        if soccerstats is not None:
            soccer_values, soccer_trace = map_soccerstats(
                soccerstats
            )

            values.update(soccer_values)
            trace.update(soccer_trace)

        _map_legacy_statshub(
            statshub,
            values,
            trace,
            warnings,
        )

        if ppi is not None:
            _map_ppi(
                ppi,
                values,
                trace,
            )

        return CanonicalMatchData(
            match=match,
            soccerstats=soccerstats,
            statshub=statshub,
            odds=odds,
            statshub_home=None,
            statshub_away=None,
            ppi=ppi,
            canonical_values=values,
            source_trace=trace,
            warnings=warnings,
        )

    if (
        soccerstats is None
        and statshub_home is None
        and statshub_away is None
        and ppi is None
        and odds is None
    ):
        raise ValueError(
            "En az bir statistics source verilmelidir."
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
