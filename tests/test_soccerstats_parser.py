from __future__ import annotations

from pathlib import Path

import pytest

from q200_engine.ingestion.soccerstats_parser import (
    SOCCERSTATS_PARSER_VERSION,
    extract_pdf_text,
    parse_soccerstats_pdf,
    parse_soccerstats_text,
)


SOCCERSTATS_SAMPLE = """\
Spain - LaLiga
Thu 17 Sep 2026 at 18:00
Real Betis vs Getafe
Points Per Game (PPG)
Home3.00 0.00Away
Goal statistics
Real Betis Getafe
HomeTotal TotalAway
2 7 Goals scored (GF) 3 0
1.001.40 GF per match 0.600.00
0 6 Goals conceded (GA) 6 4
0.001.20 GA per match 1.202.00
(A) Real Betis scoring rate at home100%
(B) Getafe scoring rate away0%
(A) Real Betis conceding rate at home0%
(B) Getafe conceding rate away100%
(A) Real Betis over 1.5 at home0%
(A) Real Betis over 2.5 at home0%
(A) Real Betis over 3.5 at home0%
(A) Real Betis BTS matches at home0%
Avg Corners For 5.00 4.00 3.00 Avg Corners Against
Avg Corners Against 7.50 5.25 3.00 Avg Corners For
Avg Total Corners (F+A) 12.50 9.25 6.00 Avg Total Corners (F+A)
Over 7.5 total corners100% 75% 50%Over 7.5 total corners
Over 8.5 total corners100% 50% 0% Over 8.5 total corners
Over 9.5 total corners50% 25% 0% Over 9.5 total corners
Over 10.5 total corners50% 25% 0% Over 10.5 total corners
Over 11.5 total corners50% 25% 0% Over 11.5 total corners
Over 12.5 total corners50% 25% 0% Over 12.5 total corners
Over 13.5 total corners50% 25% 0% Over 13.5 total corners
H2H stats: summary of encounters above
In the 14 matches above between Real Betis and Getafe, Real Betis won 6 times, 4 matches ended in a draw, Getafe won 4 times
Real Betis total goals 15
Getafe total goals 12
Real Betis goals per match 1.07
Getafe goals per match 0.86
Total goals per match 1.93
Real Betis scored 64%
Getafe scored 64%
Both teams scored 36%
Matches over 1.5 goals 64%
Matches over 2.5 goals 29%
Matches over 3.5 goals 7%
Home vs Away distribution
50% 50% % Points
29% 71% % Goals scored
0% 100% % Goals conceded
Average goal times
Real Betis Getafe
Home Total AVERAGE MINUTES Total Away
72' 55' Average minute GF 56' '
' 52' Average minute GA 72' 74'
"""


def test_parser_version_is_declared():
    assert (
        SOCCERSTATS_PARSER_VERSION
        == "Q200-SOCCERSTATS-PARSER-V1"
    )


def test_parse_soccerstats_text_extracts_match_and_goals():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert data.match.home_team == "Real Betis"
    assert data.match.away_team == "Getafe"
    assert data.match.date == "17 Sep 2026"
    assert data.match.time == "18:00"
    assert data.match.competition == "Spain - LaLiga"

    assert data.goals.home_gf == 2.0
    assert data.goals.home_ga == 0.0
    assert data.goals.away_gf == 0.0
    assert data.goals.away_ga == 4.0

    assert (
        data.goals.home_gf_per_match
        == 1.0
    )

    assert (
        data.goals.away_ga_per_match
        == 2.0
    )


def test_parse_soccerstats_text_extracts_corners():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert (
        data.corners.home_corners_for
        == 5.0
    )

    assert (
        data.corners.home_corners_against
        == 7.5
    )

    assert (
        data.corners.away_corners_for
        == 3.0
    )

    assert (
        data.corners.away_corners_against
        == 3.0
    )

    assert (
        data.corners.home_total_corners
        == 12.5
    )

    assert (
        data.corners.away_total_corners
        == 6.0
    )


def test_parse_soccerstats_text_extracts_form():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert data.form.home_ppg == 3.0
    assert data.form.away_ppg == 0.0


def test_parse_soccerstats_text_extracts_h2h():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert data.h2h.matches == 14
    assert data.h2h.home_wins == 6
    assert data.h2h.draws == 4
    assert data.h2h.away_wins == 4

    assert data.h2h.home_goals == 15.0
    assert data.h2h.away_goals == 12.0

    assert (
        data.h2h.total_goals_per_match
        == 1.93
    )

    assert data.h2h.over_2_5 == 29.0


def test_parse_soccerstats_text_extracts_distribution():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert (
        data.distribution.home_points_percentage
        == 50.0
    )

    assert (
        data.distribution.away_points_percentage
        == 50.0
    )

    assert (
        data.distribution.home_goals_percentage
        == 29.0
    )

    assert (
        data.distribution.away_goals_percentage
        == 71.0
    )

    assert (
        data.distribution.home_goals_conceded_percentage
        == 0.0
    )

    assert (
        data.distribution.away_goals_conceded_percentage
        == 100.0
    )


def test_parse_soccerstats_text_extracts_timing():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert (
        data.timing.home_average_goal_minute_for
        == 72.0
    )

    assert (
        data.timing.away_average_goal_minute_for
        == 56.0
    )

    assert (
        data.timing.home_average_goal_minute_against
        == 52.0
    )

    assert (
        data.timing.away_average_goal_minute_against
        == 74.0
    )


def test_parser_keeps_raw_sections():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert "goals" in data.raw_sections
    assert "corners" in data.raw_sections
    assert "h2h" in data.raw_sections
    assert "timing" in data.raw_sections


def test_parser_keeps_source_metadata():
    data = parse_soccerstats_text(
        SOCCERSTATS_SAMPLE
    )

    assert (
        data.source_metadata["parser"]
        == SOCCERSTATS_PARSER_VERSION
    )

    assert (
        data.source_metadata["source"]
        == "SoccerSTATS"
    )


def test_parser_rejects_non_string():
    with pytest.raises(TypeError):
        parse_soccerstats_text(
            None  # type: ignore[arg-type]
        )


def test_parser_requires_match_header():
    with pytest.raises(ValueError):
        parse_soccerstats_text(
            "Spain - LaLiga\n"
            "Goal statistics"
        )


def test_extract_pdf_text_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_pdf_text(
            Path("does-not-exist.pdf")
        )


def test_extract_pdf_text_rejects_non_pdf(
    tmp_path,
):
    path = tmp_path / "sample.txt"

    path.write_text(
        "not a pdf",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        extract_pdf_text(path)


def test_real_pdf_fixture_if_present():
    fixture = Path(
        "tests/fixtures/"
        "WEB_1789630115.pdf"
    )

    if not fixture.exists():
        pytest.skip(
            "Gerçek SoccerSTATS PDF fixture "
            "repoda bulunmuyor."
        )

    data = parse_soccerstats_pdf(
        fixture
    )

    assert (
        data.match.home_team
        == "Real Betis"
    )

    assert (
        data.match.away_team
        == "Getafe"
    )

    assert (
        data.goals.home_gf_per_match
        == 1.0
    )

    assert (
        data.goals.away_ga_per_match
        == 2.0
    )

    assert (
        data.corners.home_corners_for
        == 5.0
    )

    assert (
        data.corners.home_corners_against
        == 7.5
    )
