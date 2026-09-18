from __future__ import annotations

from q200_engine.ingestion import (
    FiveSourceMatchInput,
    MatchInfo,
    OddsData,
    PPIData,
    SoccerStatsData,
    StatsHubData,
    model_to_dict,
)


def test_five_source_input_accepts_all_five_sources():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        competition="Spain - LaLiga",
    )

    statshub_home = StatsHubData(
        match=match,
        values={
            "goals_for_avg": 1.70,
            "xg": 1.50,
            "shots_on_target": 5.65,
        },
    )

    statshub_away = StatsHubData(
        match=match,
        values={
            "goals_for_avg": 0.95,
            "xg": 0.76,
            "shots_on_target": 2.80,
        },
    )

    soccerstats = SoccerStatsData(
        match=match,
    )

    ppi = PPIData(
        match=match,
        home_ppg=2.40,
        away_ppg=1.00,
        home_ppi=2.33,
        away_ppi=1.25,
    )

    odds = OddsData(
        match=match,
        markets={
            "1x2": {
                "home": 1.72,
                "draw": 3.75,
                "away": 5.80,
            }
        },
    )

    data = FiveSourceMatchInput(
        match=match,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        soccerstats=soccerstats,
        ppi=ppi,
        odds=odds,
    )

    assert data.source_count == 5
    assert data.statistics_source_count == 4
    assert data.has_odds is True

    assert data.statshub_home is statshub_home
    assert data.statshub_away is statshub_away
    assert data.soccerstats is soccerstats
    assert data.ppi is ppi
    assert data.odds is odds


def test_five_source_input_can_exist_without_odds():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
    )

    data = FiveSourceMatchInput(
        match=match,
        statshub_home=StatsHubData(match=match),
        statshub_away=StatsHubData(match=match),
        soccerstats=SoccerStatsData(match=match),
        ppi=PPIData(match=match),
    )

    assert data.source_count == 4
    assert data.statistics_source_count == 4
    assert data.has_odds is False


def test_ppi_is_data_only_and_does_not_calculate_model_values():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
    )

    ppi = PPIData(
        match=match,
        home_ppg=2.40,
        away_ppg=1.00,
        home_ppi=2.33,
        away_ppi=1.25,
    )

    assert ppi.home_ppg == 2.40
    assert ppi.away_ppg == 1.00
    assert ppi.home_ppi == 2.33
    assert ppi.away_ppi == 1.25


def test_model_to_dict_serializes_five_source_input():
    match = MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
    )

    data = FiveSourceMatchInput(
        match=match,
        statshub_home=StatsHubData(
            match=match,
            values={"xg": 1.50},
        ),
        statshub_away=StatsHubData(
            match=match,
            values={"xg": 0.76},
        ),
        soccerstats=SoccerStatsData(
            match=match,
        ),
        ppi=PPIData(
            match=match,
            home_ppi=2.33,
            away_ppi=1.25,
        ),
        odds=OddsData(
            match=match,
            markets={
                "1x2": {
                    "home": 1.72,
                    "draw": 3.75,
                    "away": 5.80,
                }
            },
        ),
    )

    result = model_to_dict(data)

    assert result["match"]["home_team"] == "Real Betis"
    assert result["match"]["away_team"] == "Getafe"

    assert result["statshub_home"]["values"]["xg"] == 1.50
    assert result["statshub_away"]["values"]["xg"] == 0.76

    assert result["ppi"]["home_ppi"] == 2.33
    assert result["ppi"]["away_ppi"] == 1.25

    assert result["odds"]["markets"]["1x2"]["home"] == 1.72
