"""
Q200 Engine - Five Source File Loader

Q200 V3.1

Gerçek dosya/girdi kaynaklarını FiveSourceMatchInput
sözleşmesine bağlar.

Desteklenen kaynaklar:

1. StatsHub HOME image
2. StatsHub AWAY image
3. SoccerSTATS PDF
4. PPI PDF
5. Odds PDF

Akış:

StatsHub HOME ─────┐
StatsHub AWAY ─────┤
SoccerSTATS PDF ───┤
PPI PDF ───────────┤
Odds PDF ──────────┘
        ↓
FiveSourceMatchInput
        ↓
five_source_pipeline
        ↓
Q200

Bu katman:
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- Odds'u model oluşturma aşamasında kullanmaz.
- Kaynak verisini uydurmaz.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .ingestion.models import (
    FiveSourceMatchInput,
    MatchInfo,
    PPIData,
    StatsHubData,
)
from .ingestion.soccerstats_parser import (
    parse_soccerstats_pdf,
)
from .odds_pdf_reader import (
    parse_odds_pdf,
)
from .statshub_ocr import (
    create_statshub_review,
)
from .statshub_review_mapper import (
    review_to_statshub_data,
)


FIVE_SOURCE_LOADER_VERSION = (
    "Q200-FIVE-SOURCE-LOADER-V1"
)


# =========================================================
# GENERIC HELPERS
# =========================================================


def _require_file(
    path: str | Path,
    *,
    extensions: tuple[str, ...] | None = None,
) -> Path:
    """
    Dosyanın gerçekten mevcut olduğunu doğrular.
    """

    result = Path(path)

    if not result.exists():
        raise FileNotFoundError(
            f"Kaynak dosya bulunamadı: {result}"
        )

    if not result.is_file():
        raise ValueError(
            f"Kaynak yolu dosya olmalıdır: {result}"
        )

    if extensions is not None:
        if result.suffix.lower() not in extensions:
            allowed = ", ".join(extensions)

            raise ValueError(
                f"Desteklenmeyen dosya türü: "
                f"{result.suffix}. "
                f"Beklenen: {allowed}"
            )

    return result


def _norm_team(
    value: str,
) -> str:
    """
    Takım adını karşılaştırma amacıyla normalize eder.
    """

    return "".join(
        character
        for character in value.casefold()
        if character.isalnum()
    )


def _validate_match(
    expected: MatchInfo,
    actual: MatchInfo | None,
    *,
    source: str,
) -> None:
    """
    Kaynak maç kimliğini ana maç kimliğiyle karşılaştırır.
    """

    if actual is None:
        raise ValueError(
            f"{source} match bilgisi bulunamadı."
        )

    if (
        _norm_team(expected.home_team)
        != _norm_team(actual.home_team)
    ):
        raise ValueError(
            f"{source} HOME takımı eşleşmiyor: "
            f"{expected.home_team} != "
            f"{actual.home_team}"
        )

    if (
        _norm_team(expected.away_team)
        != _norm_team(actual.away_team)
    ):
        raise ValueError(
            f"{source} AWAY takımı eşleşmiyor: "
            f"{expected.away_team} != "
            f"{actual.away_team}"
        )


# =========================================================
# STATSHUB
# =========================================================


def load_statshub_image(
    image_path: str | Path,
    *,
    match: MatchInfo,
    ocr_text: str | None = None,
    ocr_engine: Any | None = None,
) -> StatsHubData:
    """
    StatsHub ekran görüntüsünü:

        IMAGE
          ↓
        OCR
          ↓
        DataReview
          ↓
        APPROVAL
          ↓
        StatsHubData

    akışından geçirir.

    ÖNEMLİ:

    StatsHub review başlangıçta onaysızdır.

    Bu nedenle loader otomatik olarak
    StatsHubData üretmeye çalışmaz.

    Kullanıcı/üst katman tarafından onaylanmış
    OCR metni veya review gerekir.
    """

    path = _require_file(
        image_path,
        extensions=(
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        ),
    )

    review = create_statshub_review(
        path,
        ocr_text=ocr_text,
        ocr_engine=ocr_engine,
    )

    if not review.approved:
        raise RuntimeError(
            "StatsHub OCR verisi henüz onaylanmamış. "
            "DataReview approval gereklidir."
        )

    data = review_to_statshub_data(
        review,
        match=match,
    )

    return data


def load_statshub_text(
    text: str,
    *,
    match: MatchInfo,
) -> StatsHubData:
    """
    Test/manuel giriş için StatsHub text'ini
    doğrudan StatsHubData'ya dönüştürür.

    Bu fonksiyon OCR approval gerektirmeyen
    kontrollü text girişidir.
    """

    from .statshub_ocr import (
        flatten_statshub_summary,
        parse_statshub_table_text,
    )

    if not isinstance(
        text,
        str,
    ):
        raise TypeError(
            "StatsHub text string olmalıdır."
        )

    if not text.strip():
        raise ValueError(
            "StatsHub text boş olamaz."
        )

    table = parse_statshub_table_text(
        text
    )

    values = flatten_statshub_summary(
        table
    )

    if not values:
        raise ValueError(
            "StatsHub text içinden veri çıkarılamadı."
        )

    return StatsHubData(
        match=match,
        values=values,
        raw_text=text,
        source_metadata={
            "source": "StatsHub",
            "loader": FIVE_SOURCE_LOADER_VERSION,
            "input_type": "text",
        },
    )


# =========================================================
# PPI
# =========================================================


def _extract_ppi_row(
    text: str,
    team: str,
) -> tuple[
    float,
    float,
    float,
]:
    """
    PPI tablosundan:

        Team PPG
        Opponents PPG
        Points Performance Index

    üçlüsünü çıkarır.

    Örnek:

        Real Betis 5 12 2.40 0.97 2.33

    sonucu:

        (2.40, 0.97, 2.33)
    """

    escaped_team = re.escape(
        team.strip()
    )

    pattern = re.compile(
        rf"{escaped_team}"
        r"\s+\d+\s+\d+\s+"
        r"(\d+(?:[.,]\d+)?)\s+"
        r"(\d+(?:[.,]\d+)?)\s+"
        r"(\d+(?:[.,]\d+)?)",
        re.IGNORECASE,
    )

    match = pattern.search(
        text
    )

    if match is None:
        raise ValueError(
            f"PPI kaynağında takım bulunamadı: {team}"
        )

    values = tuple(
        float(
            value.replace(
                ",",
                ".",
            )
        )
        for value in match.groups()
    )

    return values


def load_ppi_pdf(
    pdf_path: str | Path,
    *,
    match: MatchInfo,
) -> PPIData:
    """
    PPI PDF'sini okuyup PPIData oluşturur.

    PPI yalnızca context olarak taşınır.
    Lambda hesabına doğrudan eklenmez.
    """

    path = _require_file(
        pdf_path,
        extensions=(".pdf",),
    )

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PPI PDF okumak için pypdf gereklidir."
        ) from exc

    reader = PdfReader(
        str(path)
    )

    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    if not text.strip():
        raise ValueError(
            "PPI PDF metni boş."
        )

    home_ppg, home_opp_ppg, home_ppi = (
        _extract_ppi_row(
            text,
            match.home_team,
        )
    )

    away_ppg, away_opp_ppg, away_ppi = (
        _extract_ppi_row(
            text,
            match.away_team,
        )
    )

    return PPIData(
        match=match,
        home_ppg=home_ppg,
        away_ppg=away_ppg,
        home_ppi=home_ppi,
        away_ppi=away_ppi,
        home_opponent_ppg=home_opp_ppg,
        away_opponent_ppg=away_opp_ppg,
        raw_text=text,
        source_metadata={
            "source": "PPI",
            "loader": FIVE_SOURCE_LOADER_VERSION,
            "file": path.name,
        },
    )


# =========================================================
# COMPLETE FIVE SOURCE INPUT
# =========================================================


def build_five_source_input(
    *,
    match: MatchInfo,
    statshub_home: StatsHubData,
    statshub_away: StatsHubData,
    soccerstats_pdf: str | Path,
    ppi_pdf: str | Path,
    odds_pdf: str | Path,
) -> FiveSourceMatchInput:
    """
    Gerçek beş kaynaklı input oluşturur.

    Giriş:

        StatsHub HOME
        StatsHub AWAY
        SoccerSTATS PDF
        PPI PDF
        Odds PDF

    Çıkış:

        FiveSourceMatchInput

    Odds burada yalnızca veri taşıyıcısına
    yüklenir. Model oluşturma işlemi burada
    gerçekleştirilmez.
    """

    if not isinstance(
        match,
        MatchInfo,
    ):
        raise TypeError(
            "match MatchInfo olmalıdır."
        )

    if not isinstance(
        statshub_home,
        StatsHubData,
    ):
        raise TypeError(
            "statshub_home StatsHubData olmalıdır."
        )

    if not isinstance(
        statshub_away,
        StatsHubData,
    ):
        raise TypeError(
            "statshub_away StatsHubData olmalıdır."
        )

    _validate_match(
        match,
        statshub_home.match,
        source="StatsHub HOME",
    )

    _validate_match(
        match,
        statshub_away.match,
        source="StatsHub AWAY",
    )

    soccerstats = parse_soccerstats_pdf(
        _require_file(
            soccerstats_pdf,
            extensions=(".pdf",),
        )
    )

    _validate_match(
        match,
        soccerstats.match,
        source="SoccerSTATS",
    )

    ppi = load_ppi_pdf(
        ppi_pdf,
        match=match,
    )

    _validate_match(
        match,
        ppi.match,
        source="PPI",
    )

    odds = parse_odds_pdf(
        _require_file(
            odds_pdf,
            extensions=(".pdf",),
        )
    )

    _validate_match(
        match,
        odds.match,
        source="Odds",
    )

    return FiveSourceMatchInput(
        match=match,
        statshub_home=statshub_home,
        statshub_away=statshub_away,
        soccerstats=soccerstats,
        ppi=ppi,
        odds=odds,
        source_metadata={
            "loader": FIVE_SOURCE_LOADER_VERSION,
            "sources": [
                "StatsHub HOME",
                "StatsHub AWAY",
                "SoccerSTATS",
                "PPI",
                "Odds",
            ],
        },
    )


__all__ = [
    "FIVE_SOURCE_LOADER_VERSION",
    "load_statshub_image",
    "load_statshub_text",
    "load_ppi_pdf",
    "build_five_source_input",
]
