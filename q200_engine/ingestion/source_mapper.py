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

from dataclasses import fields
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
    Değer None değilse canonical sözlüğe ekler.
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
) -> None:
    """
    Alan mevcut değilse ekler.

    Alan zaten varsa mevcut öncelikli değer korunur.
    """

    if value is None:
        return

    if key not in values:
        values[key] = value
        trace[key] = source
        return

    warnings.append(
        f"{key}: mevcut öncelikli değer korunmuştur; "
        f"{source} değeri kullanılmadı."
    )


# ---------------------------------------------------------------------------
# Match identity
# ---------------------------------------------------------------------------


def _norm_team(value: str) -> str:
    """
    Takım adını karşılaştırma için normalize eder.
    """

    return "".join(
        character
        for character in value.casefold()
        if character.isalnum()
    )


def _validate_match_pair(
    expected: Any,
    actual: Any,
    source: str,
) -> None:
    """
    İki kaynağın HOME/AWAY takım kimliklerini kontrol eder.
    """

    if actual is None:
        raise ValueError(
            f"{source} match bilgisi bulunamadı."
        )

    if not _norm_team(
        expected.home_team
    ) == _norm_team(
        actual.home_team
    ):
        raise ValueError(
            f"{source} HOME takımı eşleşmiyor: "
            f"{expected.home_team} != {actual.home_team}"
        )

    if not _norm_team(
        expected.away_team
    ) == _norm_team(
        actual.away_team
    ):
        raise ValueError(
            f"{source} AWAY takımı eşleşmiyor: "
            f"{expected.away_team} != {actual.away_team}"
        )


# ---------------------------------------------------------------------------
# Generic dataclass mapping
# ---------------------------------------------------------------------------


def _flatten_dataclass(
    obj: Any,
    prefix: str,
    source: str,
    values: dict[str, Any],
    trace: dict[str, str],
) -> None:
    """
    Dataclass alanlarını canonical sözlüğe taşır.

    Dict/list gibi composite alanlar doğrudan flatten edilmez.
    """

    for item in fields(obj):
        value = getattr(
            obj,
            item.name,
        )

        if value is None:
            continue

        if isinstance(
            value,
            (dict, list, tuple),
        ):
            continue

        _put(
            values,
            trace,
            f"{prefix}{item.name}",
            value,
            source,
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

    IMPORTANT:

    Burada GoalStats, CornerStats, FormStats vb.
    modellerinde gerçekten bulunan alanlar kullanılır.

    Modelde olmayan alanlara erişilmez.
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

    source = "SoccerSTATS"

    # ------------------------------------------------------------------
    # Goals
    # ------------------------------------------------------------------

    _flatten_dataclass(
        data.goals,
        "",
        source,
        values,
        trace,
    )

    # ------------------------------------------------------------------
    # Corners
    # ------------------------------------------------------------------

    _flatten_dataclass(
        data.corners,
        "",
        source,
        values,
        trace,
    )

    # ------------------------------------------------------------------
    # Form
    # ------------------------------------------------------------------

    _flatten_dataclass(
        data.form,
        "",
        source,
        values,
        trace,
    )

    # ------------------------------------------------------------------
    # H2H
    # ------------------------------------------------------------------

    _flatten_dataclass(
        data.h2h,
        "h2h_",
        source,
        values,
        trace,
    )

    # ------------------------------------------------------------------
    # Distribution
    # ------------------------------------------------------------------

    _flatten_dataclass(
        data.distribution,
        "",
        source,
        values,
        trace,
    )

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------

    _flatten_dataclass(
        data.timing,
        "",
        source,
        values,
        trace,
    )

    return (
        values,
        trace,
    )


# ---------------------------------------------------------------------------
# StatsHub - Five Source
# ---------------------------------------------------------------------------


def _map_statshub_model_values(
    data: StatsHubData,
    side: str,
    values: dict[str, Any],
    trace: dict[str, str],
    warnings: list[str],
) -> None:
    """
    StatsHub HOME/AWAY verisini canonical alanlara taşır.

    Ham StatsHub alanları namespace altında korunur:

        statshub_home_*
        statshub_away_*

    Model için kullanılabilecek açık alanlar ayrıca
    canonical alanlara map edilir.
    """

    source = (
        f"StatsHub {side.upper()}"
    )

    raw = data.values

    # ------------------------------------------------------------------
    # Preserve all raw StatsHub values.
    # ------------------------------------------------------------------

    for key, value in raw.items():
        _put(
            values,
            trace,
            f"statshub_{side}_{key}",
            value,
            source,
        )

    prefix = f"{side}_"

    # ------------------------------------------------------------------
    # Explicit model mappings.
    # ------------------------------------------------------------------

    mapping = {
        "goals_for": (
            f"{prefix}gf_per_match"
        ),
        "goals_agt": (
            f"{prefix}ga_per_match"
        ),
        "xg_for": (
            f"{prefix}xg"
        ),
        "xg_agt": (
            f"{prefix}xga"
        ),
        "total_shots_for": (
            f"{prefix}total_shots_avg"
        ),
        "shots_on_target_for": (
            f"{prefix}shots_on_target_avg"
        ),
        "total_shots_avg": (
            f"{prefix}total_shots_avg"
        ),
        "goals_avg": (
            f"{prefix}goals_avg"
        ),
        "xg_avg": (
            f"{prefix}xg_avg"
        ),
    }

    for raw_key, canonical_key in mapping.items():
        _put_if_missing(
            values,
            trace,
            warnings,
            canonical_key,
            raw.get(raw_key),
            source,
        )


# ---------------------------------------------------------------------------
# StatsHub - Legacy
# ---------------------------------------------------------------------------


def _map_legacy_statshub(
    data: StatsHubData,
    values: dict[str, Any],
    trace: dict[str, str],
    warnings: list[str],
) -> None:
    """
    Eski tek StatsHub kaynağını map eder.

    StatsHubData'nın gerçek veri modeli:

        values: Dict[str, Any]

    olduğundan doğrudan data.gf gibi olmayan
    attribute'lara erişilmez.
    """

    source = "StatsHub"

    raw = data.values

    for key, value in raw.items():
        _put_if_missing(
            values,
            trace,
            warnings,
            key,
            value,
            source,
        )

    # Tek StatsHub kaynağında HOME/AWAY ayrımı
    # veri tarafından açıkça verilmedikçe uydurulmaz.


# ---------------------------------------------------------------------------
# PPI
# ---------------------------------------------------------------------------


def _map_ppi(
    data: PPIData,
    values: dict[str, Any],
    trace: dict[str, str],
) -> None:
    """
    PPI verisini context alanları olarak saklar.
    """

    source = "PPI"

    for name in (
        "home_ppg",
        "away_ppg",
        "home_ppi",
        "away_ppi",
        "home_opponent_ppg",
        "away_opponent_ppg",
        "home_rank",
        "away_rank",
    ):
        value = getattr(
            data,
            name,
        )

        _put(
            values,
            trace,
            f"ppi_{name}",
            value,
            source,
        )


# ---------------------------------------------------------------------------
# Match selection
# ---------------------------------------------------------------------------


def _select_match(
    *sources: Any,
) -> Any:
    """
    İlk geçerli match bilgisini seçer.
    """

    for source in sources:
        if source is None:
            continue

        match = getattr(
            source,
            "match",
            None,
        )

        if match is not None:
            return match

    return None


# ---------------------------------------------------------------------------
# Five Source Mapper
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
    Q200 V3.1 five-source mapper.

    Sources:

        1. StatsHub HOME
        2. StatsHub AWAY
        3. SoccerSTATS
        4. PPI
        5. Odds

    Priority:

        SoccerSTATS
            ↓
        StatsHub HOME/AWAY

    PPI:

        Context olarak saklanır.

    Odds:

        CanonicalMatchData içinde tutulur.

        canonical_values içine market odds
        değerleri yazılmaz.

    Böylece odds model oluşturma aşamasını
    etkileyemez.
    """

    sources = (
        soccerstats,
        statshub_home,
        statshub_away,
        ppi,
        odds,
    )

    if all(
        source is None
        for source in sources
    ):
        raise ValueError(
            "En az bir source verilmelidir."
        )

    # ------------------------------------------------------------------
    # Determine match identity.
    # ------------------------------------------------------------------

    match = _select_match(
        soccerstats,
        statshub_home,
        statshub_away,
        ppi,
        odds,
    )

    if match is None:
        raise ValueError(
            "Canonical data için match bilgisi gereklidir."
        )

    # ------------------------------------------------------------------
    # Validate source match identities.
    # ------------------------------------------------------------------

    source_pairs = (
        (
            soccerstats,
            "SoccerSTATS",
        ),
        (
            statshub_home,
            "StatsHub HOME",
        ),
        (
            statshub_away,
            "StatsHub AWAY",
        ),
        (
            ppi,
            "PPI",
        ),
        (
            odds,
            "Odds",
        ),
    )

    for source, source_name in source_pairs:
        if source is None:
            continue

        source_match = getattr(
            source,
            "match",
            None,
        )

        if source_match is None:
            continue

        _validate_match_pair(
            match,
            source_match,
            source_name,
        )

    canonical_values: dict[str, Any] = {}
    source_trace: dict[str, str] = {}
    warnings: list[str] = []

    # ------------------------------------------------------------------
    # 1. SoccerSTATS
    # ------------------------------------------------------------------

    if soccerstats is not None:
        soccer_values, soccer_trace = (
            map_soccerstats(
                soccerstats
            )
        )

        canonical_values.update(
            soccer_values
        )

        source_trace.update(
            soccer_trace
        )

    # ------------------------------------------------------------------
    # 2. StatsHub HOME
    # ------------------------------------------------------------------

    if statshub_home is not None:
        _map_statshub_model_values(
            statshub_home,
            "home",
            canonical_values,
            source_trace,
            warnings,
        )

    # ------------------------------------------------------------------
    # 3. StatsHub AWAY
    # ------------------------------------------------------------------

    if statshub_away is not None:
        _map_statshub_model_values(
            statshub_away,
            "away",
            canonical_values,
            source_trace,
            warnings,
        )

    # ------------------------------------------------------------------
    # 4. PPI
    # ------------------------------------------------------------------

    if ppi is not None:
        _map_ppi(
            ppi,
            canonical_values,
            source_trace,
        )

    # ------------------------------------------------------------------
    # 5. Odds
    # ------------------------------------------------------------------

    # Odds canonical_values içine yazılmaz.
    # Sadece CanonicalMatchData.odds alanında tutulur.

    return CanonicalMatchData(
        match=match,
        soccerstats=soccerstats,
        statshub=(
            statshub_home
            or statshub_away
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
# Backward Compatible Mapper
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
    Eski API + yeni five-source API.

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
    """

    # ------------------------------------------------------------------
    # Prevent ambiguous legacy/new StatsHub usage.
    # ------------------------------------------------------------------

    if (
        statshub is not None
        and (
            statshub_home is not None
            or statshub_away is not None
        )
    ):
        raise ValueError(
            "statshub ile statshub_home/"
            "statshub_away aynı anda kullanılamaz."
        )

    # ------------------------------------------------------------------
    # Legacy single StatsHub path.
    # ------------------------------------------------------------------

    if statshub is not None:

        if statshub.match is None:
            raise ValueError(
                "StatsHub match bilgisi gereklidir."
            )

        if soccerstats is not None:
            _validate_match_pair(
                statshub.match,
                soccerstats.match,
                "SoccerSTATS",
            )

        if (
            ppi is not None
            and ppi.match is not None
        ):
            _validate_match_pair(
                statshub.match,
                ppi.match,
                "PPI",
            )

        if (
            odds is not None
            and odds.match is not None
        ):
            _validate_match_pair(
                statshub.match,
                odds.match,
                "Odds",
            )

        values: dict[str, Any] = {}
        trace: dict[str, str] = {}
        warnings: list[str] = []

        # SoccerSTATS has priority.
        if soccerstats is not None:
            soccer_values, soccer_trace = (
                map_soccerstats(
                    soccerstats
                )
            )

            values.update(
                soccer_values
            )

            trace.update(
                soccer_trace
            )

        # Legacy StatsHub values fill only
        # fields that do not already exist.
        _map_legacy_statshub(
            statshub,
            values,
            trace,
            warnings,
        )

        # PPI context.
        if ppi is not None:
            _map_ppi(
                ppi,
                values,
                trace,
            )

        return CanonicalMatchData(
            match=statshub.match,
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

    # ------------------------------------------------------------------
    # New five-source path.
    # ------------------------------------------------------------------

    if all(
        source is None
        for source in (
            soccerstats,
            statshub_home,
            statshub_away,
            ppi,
            odds,
        )
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
