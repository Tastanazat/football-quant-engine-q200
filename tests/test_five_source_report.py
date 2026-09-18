"""
Q200 Engine - Five Source Report Integration Tests

Q200 V3.1

Five Source Runner
        ↓
AnalysisResult
        ↓
Q200 Report
"""

from __future__ import annotations

import json
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


ROOT = Path(__file__).resolve().parents[1]

SOCCERSTATS_PDF = (
    ROOT
    / "tests"
    / "fixtures"
    / "soccerstats"
    / "WEB_1789630115.pdf"
)

ODDS_PDF = (
    ROOT
    / "tests"
    / "fixtures"
    / "odds"
    / "WEB_1789630248.pdf"
)


STATSHUB_TEXT = """
Goals scored 1.00 0.60
Goals conceded 0.00 1.20
GF per match 1.00 0.60
GA per match 0.00 1.20
xG 1.50 1.10
xGA 0.90 1.30
"""


def make_match() -> MatchInfo:
    """
    Fixture PDF'lerde kullanılan maç kimliği.
    """

    return MatchInfo(
        home_team="Real Betis",
        away_team="Getafe",
    )


def make_statshub_image(
    tmp_path: Path,
    name: str,
) -> Path:
    """
    Test için sahte image dosyası oluşturur.

    OCR çağrısı test sırasında monkeypatch edilir.
    """

    path = tmp_path / name

    path.write_bytes(
        b"fake-statshub-image"
    )

    return path


def test_five_source_result_can_become_report(
    tmp_path,
    monkeypatch,
) -> None:
    """
    Five Source Runner çıktısının mevcut Report
    katmanına doğrudan bağlanabildiğini doğrular.
    """

    match = make_match()

    home_image = make_statshub_image(
        tmp_path,
        "statshub_home.jpg",
    )

    away_image = make_statshub_image(
        tmp_path,
        "statshub_away.jpg",
    )

    from q200_engine.five_source_loader import (
        load_statshub_image,
    )

    def fake_loader(
        image_path,
        *,
        match,
        ocr_text=None,
        ocr_engine=None,
    ):
        return load_statshub_image(
            image_path,
            match=match,
            ocr_text=STATSHUB_TEXT,
        )

    monkeypatch.setattr(
        "q200_engine.five_source_runner.load_statshub_image",
        fake_loader,
    )

    result = run_five_source_files(
        match=match,
        statshub_home_image=home_image,
        statshub_away_image=away_image,
        soccerstats_pdf=SOCCERSTATS_PDF,
        ppi_pdf=SOCCERSTATS_PDF,
        odds_pdf=ODDS_PDF,
        bankroll=50_000,
        market="1X2",
        uncertainty="MEDIUM",
        home_ocr_text=STATSHUB_TEXT,
        away_ocr_text=STATSHUB_TEXT,
    )

    assert result.snapshot.locked is True

    report = build_report(
        result
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


def test_five_source_report_json_is_valid(
    tmp_path,
    monkeypatch,
) -> None:
    """
    Five Source → AnalysisResult → JSON Report
    zincirini doğrular.
    """

    match = make_match()

    home_image = make_statshub_image(
        tmp_path,
        "home.jpg",
    )

    away_image = make_statshub_image(
        tmp_path,
        "away.jpg",
    )

    from q200_engine.five_source_loader import (
        load_statshub_image,
    )

    def fake_loader(
        image_path,
        *,
        match,
        ocr_text=None,
        ocr_engine=None,
    ):
        return load_statshub_image(
            image_path,
            match=match,
            ocr_text=STATSHUB_TEXT,
        )

    monkeypatch.setattr(
        "q200_engine.five_source_runner.load_statshub_image",
        fake_loader,
    )

    result = run_five_source_files(
        match=match,
        statshub_home_image=home_image,
        statshub_away_image=away_image,
        soccerstats_pdf=SOCCERSTATS_PDF,
        ppi_pdf=SOCCERSTATS_PDF,
        odds_pdf=ODDS_PDF,
        bankroll=50_000,
    )

    json_text = report_to_json(
        result
    )

    parsed = json.loads(
        json_text
    )

    assert (
        parsed["report_version"]
        == REPORT_VERSION
    )

    assert (
        parsed["model_locked"]
        is True
    )

    assert (
        parsed["model_version"]
        == "Q200-V3.1"
    )


def test_five_source_report_text_is_readable(
    tmp_path,
    monkeypatch,
) -> None:
    """
    Five Source analizinin kullanıcı tarafından
    okunabilir standart rapora dönüşebildiğini
    doğrular.
    """

    match = make_match()

    home_image = make_statshub_image(
        tmp_path,
        "home.jpg",
    )

    away_image = make_statshub_image(
        tmp_path,
        "away.jpg",
    )

    from q200_engine.five_source_loader import (
        load_statshub_image,
    )

    def fake_loader(
        image_path,
        *,
        match,
        ocr_text=None,
        ocr_engine=None,
    ):
        return load_statshub_image(
            image_path,
            match=match,
            ocr_text=STATSHUB_TEXT,
        )

    monkeypatch.setattr(
        "q200_engine.five_source_runner.load_statshub_image",
        fake_loader,
    )

    result = run_five_source_files(
        match=match,
        statshub_home_image=home_image,
        statshub_away_image=away_image,
        soccerstats_pdf=SOCCERSTATS_PDF,
        ppi_pdf=SOCCERSTATS_PDF,
        odds_pdf=ODDS_PDF,
        bankroll=50_000,
    )

    text = report_to_text(
        result
    )

    assert (
        "Q200 V3.1 ANALİZ RAPORU"
        in text
    )

    assert "MODEL" in text
    assert "ODDS ANALYSIS" in text
    assert "SELECTION" in text
    assert "PESSIMISTIC EV" in text
