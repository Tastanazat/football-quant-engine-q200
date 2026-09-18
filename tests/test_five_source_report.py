"""
Q200 Engine - Five Source Report Integration Tests

Q200 V3.1

Five Source Runner
        ↓
AnalysisResult
        ↓
Q200 Report
        ↓
JSON / TEXT
"""

from __future__ import annotations

from pathlib import Path

from q200_engine.five_source_runner import (
    run_five_source_files,
)
from q200_engine.ingestion.models import (
    MatchInfo,
)
from q200_engine.report import (
    REPORT_VERSION,
    build_report,
    report_to_json,
    report_to_text,
)


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent


SOCCERSTATS_PDF = (
    TESTS_DIR
    / "fixtures"
    / "soccerstats"
    / "WEB_1789630115.pdf"
)

PPI_PDF = (
    PROJECT_ROOT
    / "WEB_1789630147.pdf"
)

ODDS_PDF = (
    TESTS_DIR
    / "fixtures"
    / "odds"
    / "WEB_1789630248.pdf"
)


STATSHUB_TEXT = """
Goals 3.05 1.70 1.35 2 3 1 2 1 1 2 1 2
Corners 9.15 4.30 4.85 4 5 6 8 2 4 4 4 8
Expected Goals (xG) 2.92 1.50 1.41 3.75 1.80 0.93 1.92 0.71 1.24 1.51 0.97 1.80
Total Shots 26.50 15.05 11.45 26 20 10 20 15 18 18 7 16
Possession 100.00 50.85 49.15 38 55 42 60 58 48 64 37 45
"""


def make_match() -> MatchInfo:
    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
        date="2026-09-17",
        time="20:00",
        competition="Spain - LaLiga",
        source="Q200",
    )


def create_analysis_result(
    tmp_path,
    monkeypatch,
):
    match = make_match()

    home_image = (
        tmp_path
        / "statshub_home.jpg"
    )

    away_image = (
        tmp_path
        / "statshub_away.jpg"
    )

    home_image.write_bytes(
        b"fake-home-image"
    )

    away_image.write_bytes(
        b"fake-away-image"
    )

    def fake_statshub_loader(
        image_path,
        *,
        match,
        ocr_text=None,
        ocr_engine=None,
    ):
        from q200_engine.ingestion.models import (
            StatsHubData,
        )

        source_name = (
            "StatsHub HOME"
            if "home" in str(
                image_path
            ).lower()
            else "StatsHub AWAY"
        )

        return StatsHubData(
            match=match,
            values={
                "goals_for": 1.70,
                "goals_agt": 1.35,
                "xg_avg": 2.92,
                "total_shots_avg": 15.05,
                "shots_on_target_avg": 5.65,
            },
            raw_text=STATSHUB_TEXT,
            source_metadata={
                "source": source_name,
                "approved": True,
            },
        )

    monkeypatch.setattr(
        "q200_engine.five_source_runner.load_statshub_image",
        fake_statshub_loader,
    )

    return run_five_source_files(
        match=match,
        statshub_home_image=home_image,
        statshub_away_image=away_image,
        soccerstats_pdf=SOCCERSTATS_PDF,
        ppi_pdf=PPI_PDF,
        odds_pdf=ODDS_PDF,
        bankroll=50_000,
        market="1X2",
        uncertainty="MEDIUM",
        home_ocr_text=STATSHUB_TEXT,
        away_ocr_text=STATSHUB_TEXT,
    )


def test_five_source_result_is_locked(
    tmp_path,
    monkeypatch,
):
    result = create_analysis_result(
        tmp_path,
        monkeypatch,
    )

    assert result.snapshot.locked is True

    assert (
        result.snapshot.model_version
        == "Q200-V3.1"
    )


def test_five_source_result_builds_report(
    tmp_path,
    monkeypatch,
):
    result = create_analysis_result(
        tmp_path,
        monkeypatch,
    )

    report = build_report(
        result
    )

    assert isinstance(
        report,
        dict,
    )

    assert (
        report["report_version"]
        == REPORT_VERSION
    )

    assert (
        report["model_locked"]
        is True
    )

    assert (
        report["model_version"]
        == "Q200-V3.1"
    )

    assert "model" in report

    assert "stress_test" in report

    assert "odds_analysis" in report

    assert "selection" in report


def test_five_source_report_contains_model(
    tmp_path,
    monkeypatch,
):
    result = create_analysis_result(
        tmp_path,
        monkeypatch,
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

    assert (
        report["model"]["monte_carlo_probabilities"]
        == result.snapshot.monte_carlo_probabilities
    )


def test_five_source_report_contains_odds_analysis(
    tmp_path,
    monkeypatch,
):
    result = create_analysis_result(
        tmp_path,
        monkeypatch,
    )

    report = build_report(
        result
    )

    assert (
        report["odds_analysis"]["fair_odds"]
        == result.fair_odds
    )

    assert (
        report["odds_analysis"]["no_vig_probabilities"]
        == result.no_vig_probabilities
    )

    assert (
        report["odds_analysis"]["baseline_ev"]
        == result.ev
    )

    assert (
        report["odds_analysis"]["pessimistic_ev"]
        == result.pessimistic_ev
    )


def test_five_source_report_contains_selection(
    tmp_path,
    monkeypatch,
):
    result = create_analysis_result(
        tmp_path,
        monkeypatch,
    )

    report = build_report(
        result
    )

    selection = report[
        "selection"
    ]

    assert "selections" in selection

    assert (
        "eligible_count"
        in selection
    )

    assert (
        "total_stake"
        in selection
    )


def test_five_source_report_to_json(
    tmp_path,
    monkeypatch,
):
    result = create_analysis_result(
        tmp_path,
        monkeypatch,
    )

    text = report_to_json(
        result
    )

    assert isinstance(
        text,
        str,
    )

    assert (
        '"report_version"'
        in text
    )

    assert (
        '"model_locked": true'
        in text
    )

    assert (
        '"model_version": "Q200-V3.1"'
        in text
    )


def test_five_source_report_to_text(
    tmp_path,
    monkeypatch,
):
    result = create_analysis_result(
        tmp_path,
        monkeypatch,
    )

    text = report_to_text(
        result
    )

    assert isinstance(
        text,
        str,
    )

    assert (
        "Q200 V3.1 ANALİZ RAPORU"
        in text
    )

    assert (
        "MODEL"
        in text
    )

    assert (
        "MODEL PROBABILITIES"
        in text
    )

    assert (
        "ODDS ANALYSIS"
        in text
    )

    assert (
        "PESSIMISTIC EV"
        in text
    )

    assert (
        "SELECTION"
        in text
    )
