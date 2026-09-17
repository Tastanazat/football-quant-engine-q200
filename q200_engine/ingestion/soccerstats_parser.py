"""
Q200 Engine - SoccerSTATS PDF Parser

Q200 V3.1

SoccerSTATS PDF
        ↓
PDF Text
        ↓
Canonical SoccerStatsData

Bu katman:
- PDF okur.
- SoccerSTATS bölümlerini ayırır.
- Canonical ingestion modellerini doldurur.

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Odds kullanmaz.
- Selection yapmaz.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from .models import (
    CornerStats,
    FormStats,
    GoalStats,
    H2HStats,
    MatchInfo,
    SoccerStatsData,
    TeamDistributionStats,
    TimingStats,
)


SOCCERSTATS_PARSER_VERSION = "Q200-SOCCERSTATS-PARSER-V1"

_NUM = r"(?:\d+\.\d{1,2}|\d+)"


def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text string olmalıdır.")

    return re.sub(
        r"[ \t]+",
        " ",
        text.replace("\u00a0", " ").replace("ﬁ", "fi"),
    )


def _line(text: str, marker: str) -> str | None:
    for value in text.splitlines():
        if marker.lower() in value.lower():
            return value.strip()

    return None


def _numbers(value: str) -> list[float]:
    return [
        float(item)
        for item in re.findall(_NUM, value)
    ]


def _percent_after(
    pattern: str,
    text: str,
) -> float | None:
    match = re.search(
        pattern + rf"\s*({_NUM})%",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return float(match.group(1))


def _extract_team_names(
    text: str,
) -> tuple[str, str]:

    match = re.search(
        r"^([^\n]+?)\s+vs\s+([^\n]+?)\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )

    if not match:
        raise ValueError(
            "SoccerSTATS PDF içinde "
            "'Home vs Away' maç başlığı bulunamadı."
        )

    return (
        match.group(1).strip(),
        match.group(2).strip(),
    )


def _extract_match_info(
    text: str,
) -> MatchInfo:

    home, away = _extract_team_names(text)

    competition_match = re.search(
        r"^(.+? - .+?)$",
        text,
        re.MULTILINE,
    )

    competition = (
        competition_match.group(1).strip()
        if competition_match
        else None
    )

    date_match = re.search(
        r"\b(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\b",
        text,
    )

    time_match = re.search(
        r"\bat\s+(\d{1,2}:\d{2})",
        text,
        re.IGNORECASE,
    )

    return MatchInfo(
        home_team=home,
        away_team=away,
        date=(
            date_match.group(1)
            if date_match
            else None
        ),
        time=(
            time_match.group(1)
            if time_match
            else None
        ),
        competition=competition,
        source="SoccerSTATS",
    )


def _extract_goal_stats(
    text: str,
) -> GoalStats:

    gf_line = _line(
        text,
        "Goals scored (GF)",
    )

    ga_line = _line(
        text,
        "Goals conceded (GA)",
    )

    gfpm_line = _line(
        text,
        "GF per match",
    )

    gapm_line = _line(
        text,
        "GA per match",
    )

    gf = _numbers(gf_line or "")
    ga = _numbers(ga_line or "")
    gfpm = _numbers(gfpm_line or "")
    gapm = _numbers(gapm_line or "")

    return GoalStats(
        home_gf=(
            gf[0]
            if len(gf) >= 4
            else None
        ),
        home_ga=(
            ga[0]
            if len(ga) >= 4
            else None
        ),
        away_gf=(
            gf[3]
            if len(gf) >= 4
            else None
        ),
        away_ga=(
            ga[3]
            if len(ga) >= 4
            else None
        ),
        home_gf_per_match=(
            gfpm[0]
            if len(gfpm) >= 4
            else None
        ),
        home_ga_per_match=(
            gapm[0]
            if len(gapm) >= 4
            else None
        ),
        away_gf_per_match=(
            gfpm[3]
            if len(gfpm) >= 4
            else None
        ),
        away_ga_per_match=(
            gapm[3]
            if len(gapm) >= 4
            else None
        ),
        home_scoring_rate=_percent_after(
            r"\(A\).*?scoring rate at home",
            text,
        ),
        away_scoring_rate=_percent_after(
            r"\(B\).*?scoring rate away",
            text,
        ),
        home_conceding_rate=_percent_after(
            r"\(A\).*?conceding rate at home",
            text,
        ),
        away_conceding_rate=_percent_after(
            r"\(B\).*?conceding rate away",
            text,
        ),
        over_1_5=_percent_after(
            r"\(A\).*?over 1\.5 at home",
            text,
        ),
        over_2_5=_percent_after(
            r"\(A\).*?over 2\.5 at home",
            text,
        ),
        over_3_5=_percent_after(
            r"\(A\).*?over 3\.5 at home",
            text,
        ),
        btts=_percent_after(
            r"\(A\).*?BTS matches at home",
            text,
        ),
    )


def _extract_corner_stats(
    text: str,
) -> CornerStats:

    def startswith_line(
        marker: str,
    ) -> str | None:

        for value in text.splitlines():

            if value.strip().lower().startswith(
                marker.lower()
            ):
                return value.strip()

        return None

    for_values = _numbers(
        startswith_line(
            "Avg Corners For"
        )
        or ""
    )

    against_values = _numbers(
        startswith_line(
            "Avg Corners Against"
        )
        or ""
    )

    total_values = _numbers(
        startswith_line(
            "Avg Total Corners (F+A)"
        )
        or ""
    )

    return CornerStats(
        home_corners_for=(
            for_values[0]
            if len(for_values) >= 3
            else None
        ),
        away_corners_for=(
            for_values[2]
            if len(for_values) >= 3
            else None
        ),
        home_corners_against=(
            against_values[0]
            if len(against_values) >= 3
            else None
        ),
        away_corners_against=(
            against_values[2]
            if len(against_values) >= 3
            else None
        ),
        home_total_corners=(
            total_values[0]
            if len(total_values) >= 3
            else None
        ),
        away_total_corners=(
            total_values[2]
            if len(total_values) >= 3
            else None
        ),
        over_7_5=_percent_after(
            r"Over 7\.5 total corners",
            text,
        ),
        over_8_5=_percent_after(
            r"Over 8\.5 total corners",
            text,
        ),
        over_9_5=_percent_after(
            r"Over 9\.5 total corners",
            text,
        ),
        over_10_5=_percent_after(
            r"Over 10\.5 total corners",
            text,
        ),
        over_11_5=_percent_after(
            r"Over 11\.5 total corners",
            text,
        ),
        over_12_5=_percent_after(
            r"Over 12\.5 total corners",
            text,
        ),
        over_13_5=_percent_after(
            r"Over 13\.5 total corners",
            text,
        ),
    )


def _extract_form(
    text: str,
) -> FormStats:

    match = re.search(
        r"Points Per Game \(PPG\)\s+"
        r"Home\s*"
        + _NUM
        + r"\s+"
        + _NUM
        + r"\s*Away",
        text,
        re.IGNORECASE,
    )

    if not match:
        return FormStats()

    values = _numbers(match.group(0))

    return FormStats(
        home_ppg=(
            values[-2]
            if len(values) >= 2
            else None
        ),
        away_ppg=(
            values[-1]
            if len(values) >= 2
            else None
        ),
    )


def _extract_h2h(
    text: str,
) -> H2HStats:

    block_match = re.search(
        r"H2H stats: summary of encounters above"
        r"(.*?)(?:LEAGUESMATCHES|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    block = (
        block_match.group(1)
        if block_match
        else ""
    )

    def line_value(
        prefix: str,
    ) -> float | None:

        for line in block.splitlines():

            if line.strip().lower().startswith(
                prefix.lower()
            ):

                values = _numbers(line)

                return (
                    values[-1]
                    if values
                    else None
                )

        return None

    summary = re.search(
        r"In the (\d+) matches above.*?"
        r"Real Betis won (\d+) times,\s*"
        r"(\d+) matches ended in a draw,\s*"
        r"Getafe won (\d+) times",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    matches = (
        int(summary.group(1))
        if summary
        else None
    )

    home_wins = (
        int(summary.group(2))
        if summary
        else None
    )

    draws = (
        int(summary.group(3))
        if summary
        else None
    )

    away_wins = (
        int(summary.group(4))
        if summary
        else None
    )

    return H2HStats(
        matches=matches,
        home_wins=home_wins,
        draws=draws,
        away_wins=away_wins,
        home_goals=line_value(
            "Real Betis total goals"
        ),
        away_goals=line_value(
            "Getafe total goals"
        ),
        home_goals_per_match=line_value(
            "Real Betis goals per match"
        ),
        away_goals_per_match=line_value(
            "Getafe goals per match"
        ),
        total_goals_per_match=line_value(
            "Total goals per match"
        ),
        home_scored_rate=line_value(
            "Real Betis scored"
        ),
        away_scored_rate=line_value(
            "Getafe scored"
        ),
        btts_rate=line_value(
            "Both teams scored"
        ),
        over_1_5=line_value(
            "Matches over 1.5 goals"
        ),
        over_2_5=line_value(
            "Matches over 2.5 goals"
        ),
        over_3_5=line_value(
            "Matches over 3.5 goals"
        ),
    )


def _extract_distribution(
    text: str,
) -> TeamDistributionStats:

    block_match = re.search(
        r"Home vs Away distribution"
        r"(.*?)(?:Current Streaks|LEAGUESMATCHES|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    block = (
        block_match.group(1)
        if block_match
        else ""
    )

    def row(
        label: str,
    ) -> tuple[
        float | None,
        float | None,
    ]:

        match = re.search(
            rf"({_NUM})%\s+({_NUM})%"
            rf"\s+.*?{re.escape(label)}",
            block,
            re.IGNORECASE,
        )

        if not match:
            return None, None

        return (
            float(match.group(1)),
            float(match.group(2)),
        )

    points = row("% Points")
    goals = row("% Goals scored")
    conceded = row("% Goals conceded")

    return TeamDistributionStats(
        home_points_percentage=points[0],
        away_points_percentage=points[1],
        home_goals_percentage=goals[0],
        away_goals_percentage=goals[1],
        home_goals_conceded_percentage=conceded[0],
        away_goals_conceded_percentage=conceded[1],
    )


def _extract_timing(
    text: str,
) -> TimingStats:

    block_match = re.search(
        r"Average goal times"
        r"(.*?)(?:Outcome scenarios|LEAGUESMATCHES|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    block = (
        block_match.group(1)
        if block_match
        else ""
    )

    gf_line = _line(
        block,
        "Average minute GF",
    )

    ga_line = _line(
        block,
        "Average minute GA",
    )

    gf = _numbers(gf_line or "")
    ga = _numbers(ga_line or "")

    return TimingStats(
        home_average_goal_minute_for=(
            gf[0]
            if len(gf) >= 3
            else None
        ),
        away_average_goal_minute_for=(
            gf[2]
            if len(gf) >= 3
            else None
        ),
        home_average_goal_minute_against=(
            ga[0]
            if len(ga) >= 3
            else None
        ),
        away_average_goal_minute_against=(
            ga[2]
            if len(ga) >= 3
            else None
        ),
    )


def parse_soccerstats_text(
    text: str,
) -> SoccerStatsData:
    """
    Parse extracted SoccerSTATS text.

    PDF okuma yapılmadan parser test edilebilmesi
    için text parser ayrı tutulur.
    """

    clean = _clean_text(text)

    match = _extract_match_info(clean)

    sections: dict[str, Any] = {}

    markers = {
        "goals": "Goal statistics",
        "corners": "Avg Corners For",
        "form": "Points Per Game (PPG)",
        "h2h": "H2H stats: summary of encounters above",
        "distribution": "Home vs Away distribution",
        "timing": "Average goal times",
    }

    for name, marker in markers.items():

        index = clean.lower().find(
            marker.lower()
        )

        if index >= 0:
            sections[name] = clean[
                index:index + 2500
            ]

    return SoccerStatsData(
        match=match,
        goals=_extract_goal_stats(clean),
        corners=_extract_corner_stats(clean),
        form=_extract_form(clean),
        h2h=_extract_h2h(clean),
        distribution=_extract_distribution(clean),
        timing=_extract_timing(clean),
        raw_sections=sections,
        source_metadata={
            "parser": SOCCERSTATS_PARSER_VERSION,
            "source": "SoccerSTATS",
        },
    )


def extract_pdf_text(
    pdf_path: str | Path,
) -> str:
    """Extract text from a SoccerSTATS PDF."""

    path = Path(pdf_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"PDF bulunamadı: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            "SoccerSTATS parser yalnızca PDF kabul eder."
        )

    reader = PdfReader(str(path))

    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    if not text.strip():
        raise ValueError(
            "PDF içinden okunabilir metin çıkarılamadı."
        )

    return text


def parse_soccerstats_pdf(
    pdf_path: str | Path,
) -> SoccerStatsData:
    """Read and parse a SoccerSTATS PDF."""

    return parse_soccerstats_text(
        extract_pdf_text(pdf_path)
    )


__all__ = [
    "SOCCERSTATS_PARSER_VERSION",
    "extract_pdf_text",
    "parse_soccerstats_text",
    "parse_soccerstats_pdf",
  ]
