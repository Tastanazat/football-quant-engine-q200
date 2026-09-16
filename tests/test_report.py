"""
Q200 Engine - Reporting Layer Tests

Q200 V3.1
"""

from __future__ import annotations

import json

import pytest

from q200_engine.analyzer import run_q200_from_files

from q200_engine.report import (
    REPORT_VERSION,
    build_report,
    report_to_json,
    report_to_text,
)


def create_csv(
    path,
    content,
):
    path.write_text(
        content,
        encoding="utf-8",
    )


def create_analysis_result(
    tmp_path,
):
    statistics_1 = (
        tmp_path
        / "statistics_1.csv"
    )

    statistics_2 = (
        tmp_path
        / "statistics_2.csv"
    )

    odds = (
        tmp_path
        / "odds.csv"
    )

    create_csv(
        statistics_1,
        (
            "home_gf,home_ga,away_gf\n"
            "1.80,1.10,1.40\n"
        ),
    )

    create_csv(
        statistics_2,
        (
            "away_ga,home_xg,home_xga,away_xga\n"
            "1.30,1.75,1.05,1.25\n"
        ),
    )

    create_csv(
        odds,
        (
            "outcome,odds\n"
            "HOME,2.10\n"
            "DRAW,3.40\n"
            "AWAY,3.80\n"
        ),
    )

    return run_q200_from_files(
        statistics_1,
        statistics_2,
        odds,
        bankroll=50_000,
    )


def test_build_report_contains_core_sections(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    report = build_report(
        result
    )

    assert (
        report["report_version"]
        == REPORT_VERSION
    )

    assert (
        report["model_version"]
        == "Q200-V3.1"
    )

    assert (
        report["model_locked"]
        is True
    )

    assert "model" in report
    assert "stress_test" in report
    assert "odds_analysis" in report
    assert "selection" in report


def test_build_report_contains_model_values(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    report = build_report(
        result
    )

    assert (
        report["model"]["lambda_home"]
        == result.snapshot.lambda_home
    )

    assert (
        report["model"]["lambda_away"]
        == result.snapshot.lambda_away
    )

    assert (
        report["model"]["probabilities"]
        == result.snapshot.probabilities
    )


def test_build_report_contains_odds_analysis(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    report = build_report(
        result
    )

    assert (
        report["odds_analysis"]["fair_odds"]
        == result.fair_odds
    )

    assert (
        report["odds_analysis"]["baseline_ev"]
        == result.ev
    )

    assert (
        report["odds_analysis"]["pessimistic_ev"]
        == result.pessimistic_ev
    )


def test_build_report_contains_selection_summary(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    report = build_report(
        result
    )

    selections = (
        report["selection"]["selections"]
    )

    eligible_count = sum(
        1
        for selection in selections
        if selection.get(
            "eligible"
        ) is True
    )

    assert (
        report["selection"]["eligible_count"]
        == eligible_count
    )

    expected_stake = sum(
        float(
            selection.get(
                "stake",
                0.0,
            )
        )
        for selection in selections
        if selection.get(
            "eligible"
        ) is True
    )

    assert (
        report["selection"]["total_stake"]
        == expected_stake
    )


def test_build_report_does_not_mutate_result(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    before = {
        "fair_odds": dict(
            result.fair_odds
        ),

        "ev": dict(
            result.ev
        ),

        "pessimistic_ev": dict(
            result.pessimistic_ev
        ),

        "selections": [
            dict(item)
            for item in result.selections
        ],
    }

    build_report(
        result
    )

    assert (
        result.fair_odds
        == before["fair_odds"]
    )

    assert (
        result.ev
        == before["ev"]
    )

    assert (
        result.pessimistic_ev
        == before["pessimistic_ev"]
    )

    assert (
        result.selections
        == before["selections"]
    )


def test_report_to_json_is_valid_json(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    text = report_to_json(
        result
    )

    parsed = json.loads(
        text
    )

    assert (
        parsed["report_version"]
        == REPORT_VERSION
    )

    assert (
        parsed["model_locked"]
        is True
    )


def test_report_to_json_handles_infinite_fair_odds(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    result.fair_odds[
        "ZERO_PROBABILITY"
    ] = float("inf")

    text = report_to_json(
        result
    )

    parsed = json.loads(
        text
    )

    assert (
        parsed["odds_analysis"]
        ["fair_odds"]
        ["ZERO_PROBABILITY"]
        == "Infinity"
    )


def test_report_to_json_rejects_invalid_indent(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    with pytest.raises(
        ValueError
    ):
        report_to_json(
            result,
            indent=-1,
        )


def test_report_to_json_rejects_non_integer_indent(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    with pytest.raises(
        TypeError
    ):
        report_to_json(
            result,
            indent="2",
        )


def test_report_to_text_contains_main_sections(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    text = report_to_text(
        result
    )

    assert (
        "Q200 V3.1 ANALİZ RAPORU"
        in text
    )

    assert "MODEL" in text
    assert "MODEL PROBABILITIES" in text
    assert "MONTE CARLO" in text
    assert "ODDS ANALYSIS" in text
    assert "PESSIMISTIC EV" in text
    assert "SELECTION" in text


def test_report_to_text_contains_lambdas(
    tmp_path,
):
    result = create_analysis_result(
        tmp_path
    )

    text = report_to_text(
        result
    )

    assert (
        f"{result.snapshot.lambda_home:.6f}"
        in text
    )

    assert (
        f"{result.snapshot.lambda_away:.6f}"
        in text
    )


def test_report_rejects_invalid_result():
    with pytest.raises(
        TypeError
    ):
        build_report(None)

    with pytest.raises(
        TypeError
    ):
        report_to_json(None)

    with pytest.raises(
        TypeError
    ):
        report_to_text(None)
