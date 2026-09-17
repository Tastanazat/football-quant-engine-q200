from __future__ import annotations

from q200_engine.ingestion import (
    CanonicalMatchData,
    CornerStats,
    GoalStats,
    H2HStats,
    MatchInfo,
    SoccerStatsData,
    model_to_dict,
)


def test_match_info_stores_basic_match_information():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="17 Sep 2026",
        time="18:00",
        competition="Spain - LaLiga",
        source="SoccerSTATS",
    )

    assert match.home_team == "Real Betis"
    assert match.away_team == "Getafe"
    assert match.date == "17 Sep 2026"
    assert match.time == "18:00"
    assert match.competition == "Spain - LaLiga"
    assert match.source == "SoccerSTATS"


def test_goal_stats_supports_home_and_away_values():
    goals = GoalStats(
        home_gf_per_match=1.00,
        home_ga_per_match=0.00,
        away_gf_per_match=0.00,
        away_ga_per_match=2.00,
        home_scoring_rate=100.0,
        away_scoring_rate=0.0,
        home_conceding_rate=0.0,
        away_conceding_rate=100.0,
        over_1_5=25.0,
        over_2_5=25.0,
        over_3_5=0.0,
        btts=0.0,
    )

    assert goals.home_gf_per_match == 1.00
    assert goals.home_ga_per_match == 0.00
    assert goals.away_gf_per_match == 0.00
    assert goals.away_ga_per_match == 2.00
    assert goals.home_scoring_rate == 100.0
    assert goals.away_conceding_rate == 100.0


def test_corner_stats_keeps_for_and_against_separately():
    corners = CornerStats(
        home_corners_for=5.00,
        home_corners_against=7.50,
        away_corners_for=3.00,
        away_corners_against=3.00,
        home_total_corners=12.50,
        away_total_corners=6.00,
    )

    assert corners.home_corners_for == 5.00
    assert corners.home_corners_against == 7.50
    assert corners.away_corners_for == 3.00
    assert corners.away_corners_against == 3.00
    assert corners.home_total_corners == 12.50
    assert corners.away_total_corners == 6.00


def test_h2h_stats_keeps_match_history_summary():
    h2h = H2HStats(
        matches=14,
        home_wins=6,
        draws=4,
        away_wins=4,
        home_goals=15,
        away_goals=12,
        home_goals_per_match=1.07,
        away_goals_per_match=0.86,
        total_goals_per_match=1.93,
        home_scored_rate=64.0,
        away_scored_rate=64.0,
        btts_rate=36.0,
        over_1_5=64.0,
        over_2_5=29.0,
        over_3_5=7.0,
    )

    assert h2h.matches == 14
    assert h2h.home_wins == 6
    assert h2h.draws == 4
    assert h2h.away_wins == 4
    assert h2h.home_goals == 15
    assert h2h.away_goals == 12


def test_soccerstats_data_combines_sections_without_model_calculation():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        source="SoccerSTATS",
    )

    data = SoccerStatsData(
        match=match,
        goals=GoalStats(
            home_gf_per_match=1.00,
            home_ga_per_match=0.00,
            away_gf_per_match=0.00,
            away_ga_per_match=2.00,
        ),
        corners=CornerStats(
            home_corners_for=5.00,
            home_corners_against=7.50,
            away_corners_for=3.00,
            away_corners_against=3.00,
        ),
        raw_sections={
            "goals": "SoccerSTATS goals section",
            "corners": "SoccerSTATS corners section",
        },
    )

    assert data.match.home_team == "Real Betis"
    assert data.match.away_team == "Getafe"
    assert data.goals.home_gf_per_match == 1.00
    assert data.goals.away_ga_per_match == 2.00
    assert data.corners.home_corners_for == 5.00
    assert data.corners.away_corners_for == 3.00
    assert "goals" in data.raw_sections
    assert "corners" in data.raw_sections


def test_model_to_dict_serializes_nested_dataclasses():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        source="SoccerSTATS",
    )

    data = SoccerStatsData(
        match=match,
        goals=GoalStats(
            home_gf_per_match=1.00,
            away_ga_per_match=2.00,
        ),
        corners=CornerStats(
            home_corners_for=5.00,
            away_corners_for=3.00,
        ),
    )

    result = model_to_dict(data)

    assert isinstance(result, dict)
    assert result["match"]["home_team"] == "Real Betis"
    assert result["match"]["away_team"] == "Getafe"
    assert result["goals"]["home_gf_per_match"] == 1.00
    assert result["corners"]["home_corners_for"] == 5.00


def test_canonical_match_data_keeps_source_trace():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
    )

    canonical = CanonicalMatchData(
        match=match,
        canonical_values={
            "home_gf_per_match": 1.00,
            "away_ga_per_match": 2.00,
        },
        source_trace={
            "home_gf_per_match": "SoccerSTATS",
            "away_ga_per_match": "SoccerSTATS",
        },
    )

    assert canonical.canonical_values["home_gf_per_match"] == 1.00
    assert canonical.canonical_values["away_ga_per_match"] == 2.00
    assert canonical.source_trace["home_gf_per_match"] == "SoccerSTATS"
