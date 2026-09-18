"""
Q200 Engine - Five Source History Integration Tests

Q200 V3.1

Five Source
    ↓
AnalysisResult
    ↓
Report
    ↓
AnalysisHistory
    ↓
SQLite
"""

from __future__ import annotations

from pathlib import Path

from q200_engine.five_source_runner import (
    run_five_source_files,
)
from q200_engine.history import (
    AnalysisHistory,
)
from q200_engine.ingestion.models import (
    MatchInfo,
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


def create_five_source_result(
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


def test_five_source_result_can_be_saved_to_history(
    tmp_path,
    monkeypatch,
):
    result = create_five_source_result(
        tmp_path,
        monkeypatch,
    )

    assert result.snapshot.locked is True

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "REAL-BETIS-vs-GETAFE-2026-09-17",
    )

    assert record_id == 1

    assert history.count() == 1

    record = history.get(
        record_id
    )

    assert record is not None

    assert (
        record["match_id"]
        == "REAL-BETIS-vs-GETAFE-2026-09-17"
    )

    assert (
        record["model_version"]
        == "Q200-V3.1"
    )

    assert (
        record["report_version"]
        == "Q200-REPORT-V1"
    )

    assert (
        record["result_recorded"]
        is False
    )

    assert (
        record["settlement_recorded"]
        is False
    )

    assert (
        record["report"]["model_locked"]
        is True
    )


def test_five_source_history_result_and_settlement(
    tmp_path,
    monkeypatch,
):
    result = create_five_source_result(
        tmp_path,
        monkeypatch,
    )

    history = AnalysisHistory(
        tmp_path
        / "history.sqlite"
    )

    record_id = history.save(
        result,
        "REAL-BETIS-vs-GETAFE-2026-09-17",
    )

    recorded = history.record_result(
        record_id,
        2,
        1,
    )

    assert recorded is True

    record = history.get(
        record_id
    )

    assert record is not None

    assert (
        record["result_recorded"]
        is True
    )

    assert (
        record["home_goals"]
        == 2
    )

    assert (
        record["away_goals"]
        == 1
    )

    settlement = history.settle_record(
        record_id
    )

    assert isinstance(
        settlement,
        dict,
    )

    assert (
        settlement["record_id"]
        == record_id
    )

    updated = history.get(
        record_id
    )

    assert updated is not None

    assert (
        updated["settlement_recorded"]
        is True
    )

    assert (
        updated["settlement"]
        is not None
    )


def test_five_source_history_persists_between_instances(
    tmp_path,
    monkeypatch,
):
    result = create_five_source_result(
        tmp_path,
        monkeypatch,
    )

    db = (
        tmp_path
        / "history.sqlite"
    )

    first = AnalysisHistory(
        db
    )

    record_id = first.save(
        result,
        "REAL-BETIS-vs-GETAFE-2026-09-17",
    )

    second = AnalysisHistory(
        db
    )

    record = second.get(
        record_id
    )

    assert record is not None

    assert (
        record["match_id"]
        == "REAL-BETIS-vs-GETAFE-2026-09-17"
    )

    assert second.count() == 1
