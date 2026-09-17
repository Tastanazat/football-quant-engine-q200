"""
Q200 Engine - Odds PDF Reader

Q200 V3.1

Odds PDF
    ↓
OddsData

Bu katman yalnızca Odds PDF verisini okur.

ÖNEMLİ:
- Model oluşturmaz.
- Lambda hesaplamaz.
- Poisson çalıştırmaz.
- Monte Carlo çalıştırmaz.
- No-Vig hesaplamaz.
- Fair Odds hesaplamaz.
- EV hesaplamaz.
- Kelly hesaplamaz.

Odds yalnızca model LOCK sonrasında kullanılmak üzere
ayrı bir veri yapısında tutulur.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from .ingestion.models import MatchInfo, OddsData


ODDS_PDF_READER_VERSION = "Q200-ODDS-PDF-READER-V1"


_MONTHS = {
    "ocak": "01",
    "şubat": "02",
    "mart": "03",
    "nisan": "04",
    "mayıs": "05",
    "haziran": "06",
    "temmuz": "07",
    "ağustos": "08",
    "eylül": "09",
    "ekim": "10",
    "kasım": "11",
    "aralık": "12",
}


_NUMBER = r"\d+(?:\.\d+)?"


def _odd(value: str) -> float:
    """
    Odds değerini güvenli şekilde doğrular.
    """

    odd = float(value)

    if not math.isfinite(odd):
        raise ValueError(
            f"Odds sonlu bir sayı olmalıdır: {value}"
        )

    if odd <= 1.0:
        raise ValueError(
            f"Odds 1.00'dan büyük olmalıdır: {value}"
        )

    return odd


def _extract_match_info(
    text: str,
) -> MatchInfo:
    """
    Odds PDF içinden maç bilgisini çıkarır.

    Gerçek PDF extraction sonucunda bazen:

        Real Betis - GetafeReal Betis - Getafe

    gibi tekrarlar oluşabildiği için ikinci tekrar temizlenir.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    match_line = next(
        (
            line
            for line in lines[:10]
            if " - " in line
        ),
        None,
    )

    if match_line is None:
        raise ValueError(
            "Odds PDF maç bilgisi bulunamadı."
        )

    home, away = (
        part.strip()
        for part in match_line.split(
            " - ",
            1,
        )
    )

    repeated_marker = (
        f"{home} - "
    )

    repeated_index = away.rfind(
        repeated_marker
    )

    if repeated_index >= 0:
        away = away[
            repeated_index
            + len(repeated_marker):
        ].strip()

    elif away.startswith(home):
        away = away[
            len(home):
        ].strip(" -")

    if not home or not away:
        raise ValueError(
            "Odds PDF takım isimleri bulunamadı."
        )

    date = None

    date_match = re.search(
        r"(\d{1,2})\s+"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+"
        r"(\d{4})",
        text,
    )

    if date_match:
        day, month_name, year = (
            date_match.groups()
        )

        month = _MONTHS.get(
            month_name.lower()
        )

        if month:
            date = (
                f"{year}-"
                f"{month}-"
                f"{int(day):02d}"
            )

    time_match = re.search(
        r"\b(\d{1,2}:\d{2})\b",
        text,
    )

    time = (
        time_match.group(1)
        if time_match
        else None
    )

    return MatchInfo(
        home_team=home,
        away_team=away,
        date=date,
        time=time,
        source="OddsPDF",
    )


def _section(
    text: str,
    start: str,
    ends: tuple[str, ...],
) -> str:
    """
    PDF içinden belirli bir market bölümünü çıkarır.
    """

    start_index = text.find(start)

    if start_index < 0:
        return ""

    section = text[start_index:]

    end_index = len(section)

    for marker in ends:

        marker_index = section.find(
            marker,
            len(start),
        )

        if marker_index >= 0:
            end_index = min(
                end_index,
                marker_index,
            )

    return section[:end_index]


def _parse_1x2(
    text: str,
) -> dict[str, float] | None:
    """
    Ana Maç Sonucu marketini okur.
    """

    section = _section(
        text,
        "Maç Sonucu\n",
        (
            "Maç Sonucu "
            "(2 Gol Farkta Erken Ödeme)",
            "Çifte Şans",
        ),
    )

    match = re.search(
        rf"1\s+({_NUMBER})"
        rf"\s+X\s+({_NUMBER})"
        rf"\s+2\s+({_NUMBER})",
        section,
    )

    if not match:
        return None

    return {
        "HOME": _odd(match.group(1)),
        "DRAW": _odd(match.group(2)),
        "AWAY": _odd(match.group(3)),
    }


def _parse_total(
    text: str,
    title: str,
    ends: tuple[str, ...],
    prefix: str,
) -> dict[str, dict[str, float]]:
    """
    Üst/Alt marketlerini okur.
    """

    section = _section(
        text,
        title,
        ends,
    )

    result: dict[
        str,
        dict[str, float],
    ] = {}

    for line in section.splitlines():

        match = re.search(
            rf"Üst\s+({_NUMBER})"
            rf"\s+({_NUMBER})"
            rf"\s+Alt\s+({_NUMBER})"
            rf"\s+({_NUMBER})",
            line,
        )

        if not match:
            continue

        (
            threshold,
            over,
            under_threshold,
            under,
        ) = match.groups()

        if threshold != under_threshold:
            continue

        result[
            f"{prefix}_{threshold}"
        ] = {
            "OVER": _odd(over),
            "UNDER": _odd(under),
        }

    return result


def extract_odds_pdf_text(
    pdf_path: str | Path,
) -> str:
    """
    Odds PDF dosyasından metin çıkarır.
    """

    path = Path(pdf_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Odds PDF bulunamadı: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            "Odds reader yalnızca PDF kabul eder: "
            f"{path}"
        )

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError(
            "Odds PDF okumak için pypdf gereklidir."
        ) from exc

    reader = PdfReader(
        str(path)
    )

    pages: list[str] = []

    for page in reader.pages:

        page_text = (
            page.extract_text()
            or ""
        )

        if page_text:
            pages.append(page_text)

    text = "\n".join(pages)

    if not text.strip():
        raise ValueError(
            "Odds PDF metni boş."
        )

    return text.replace(
        "\r",
        "\n",
    )


def parse_odds_pdf_text(
    text: str,
) -> OddsData:
    """
    Çıkarılmış Odds PDF metnini OddsData'ya dönüştürür.
    """

    if not isinstance(
        text,
        str,
    ):
        raise TypeError(
            "text string olmalıdır."
        )

    markets: dict[
        str,
        dict[str, float],
    ] = {}

    match_result = _parse_1x2(
        text
    )

    if match_result is not None:
        markets["1X2"] = (
            match_result
        )

    markets.update(
        _parse_total(
            text,
            "Toplam Goller\n",
            (
                "Karşılıklı Gol Olur",
            ),
            "TOTAL_GOALS",
        )
    )

    btts_section = _section(
        text,
        "Karşılıklı Gol Olur\n",
        (
            "Karşılıklı Gol Olur veya",
            "Beraberlikte İade",
        ),
    )

    btts_match = re.search(
        rf"Evet\s+({_NUMBER})"
        rf"\s+Hayır\s+({_NUMBER})",
        btts_section,
    )

    if btts_match:

        markets["BTTS"] = {
            "YES": _odd(
                btts_match.group(1)
            ),
            "NO": _odd(
                btts_match.group(2)
            ),
        }

    markets.update(
        _parse_total(
            text,
            "Toplam Kornerler\n",
            (
                "Toplam Kornerler 3-Yönlü",
                "1. Yarı - Toplam Kornerler",
            ),
            "TOTAL_CORNERS",
        )
    )

    if not markets:
        raise ValueError(
            "Odds PDF içinde desteklenen "
            "market bulunamadı."
        )

    return OddsData(
        match=_extract_match_info(
            text
        ),
        markets=markets,
        raw_text=text,
        source_metadata={
            "parser": (
                ODDS_PDF_READER_VERSION
            ),
            "source": "OddsPDF",
        },
    )


def parse_odds_pdf(
    pdf_path: str | Path,
) -> OddsData:
    """
    Odds PDF → OddsData.
    """

    text = extract_odds_pdf_text(
        pdf_path
    )

    return parse_odds_pdf_text(
        text
    )


def odds_data_to_market(
    data: OddsData,
    market: str,
) -> dict[str, float]:
    """
    OddsData içinden belirli bir marketi çıkarır.
    """

    if not isinstance(
        data,
        OddsData,
    ):
        raise TypeError(
            "data OddsData olmalıdır."
        )

    key = str(
        market
    ).strip().upper()

    if key not in data.markets:
        raise KeyError(
            f"Odds market bulunamadı: {market}"
        )

    return dict(
        data.markets[key]
    )


__all__ = [
    "ODDS_PDF_READER_VERSION",
    "extract_odds_pdf_text",
    "parse_odds_pdf_text",
    "parse_odds_pdf",
    "odds_data_to_market",
]
