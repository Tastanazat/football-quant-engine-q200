"""
Q200 Engine - Odds PDF Reader

Q200 V3.1

Odds PDF
    ↓
OddsData

Bu katman yalnızca oran PDF'sini okur.

ÖNEMLİ:
- Model oluşturmaz.
- Lambda hesaplamaz.
- Statistics kullanmaz.
- No-Vig hesaplamaz.
- EV hesaplamaz.
- Kelly hesaplamaz.

Görevi:
Odds PDF → OddsData
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from .ingestion.models import MatchInfo, OddsData


ODDS_PDF_READER_VERSION = "Q200-ODDS-PDF-READER-V1"


# =========================================================
# MONTHS
# =========================================================

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


_FLOAT = r"\d+(?:\.\d+)?"


# =========================================================
# ODDS VALIDATION
# =========================================================

def _validate_odd(
    value: str | float,
) -> float:
    """
    Odds değerini doğrular.
    """

    try:
        odd = float(value)

    except (TypeError, ValueError) as exc:

        raise ValueError(
            f"Geçersiz oran: {value}"
        ) from exc

    if not math.isfinite(odd):

        raise ValueError(
            f"Oran finite olmalıdır: {value}"
        )

    if odd <= 1.0:

        raise ValueError(
            f"Oran 1.00'dan büyük olmalıdır: {value}"
        )

    return odd


# =========================================================
# MATCH INFORMATION
# =========================================================

def _extract_match_info(
    text: str,
) -> MatchInfo:
    """
    Odds PDF'den maç bilgilerini çıkarır.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    match_line = next(
        (
            line
            for line in lines
            if " - " in line
        ),
        None,
    )

    if match_line is None:

        raise ValueError(
            "Odds PDF maç bilgisi bulunamadı."
        )

    parts = [
        part.strip()
        for part in match_line.split(" - ")
    ]

    # PDF extraction bazen:
    #
    # Real Betis - GetafeReal Betis - Getafe
    #
    # şeklinde tekrar üretebilir.
    if (
        len(parts) >= 3
        and parts[1]
        in {
            parts[0] + parts[-1],
            parts[-1] + parts[0],
        }
    ):

        home = parts[0]
        away = parts[-1]

    else:

        home, away = (
            part.strip()
            for part in match_line.split(
                " - ",
                1,
            )
        )

        # Genel tekrar koruması.
        if away.startswith(home):

            remainder = (
                away[len(home):]
                .strip()
            )

            if remainder.startswith("-"):

                remainder = (
                    remainder[1:]
                    .strip()
                )

            if remainder:

                away = remainder

    if not home or not away:

        raise ValueError(
            "Odds PDF takım isimleri bulunamadı."
        )

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    time = None

    time_match = re.search(
        r"\b(\d{1,2}:\d{2})\b",
        text,
    )

    if time_match:

        time = time_match.group(1)

    return MatchInfo(
        home_team=home,
        away_team=away,
        date=date,
        time=time,
        source="OddsPDF",
    )


# =========================================================
# SECTION EXTRACTION
# =========================================================

def _section(
    text: str,
    start: str,
    end_markers: tuple[str, ...],
) -> str:
    """
    PDF text içerisinden belirli market bölümünü çıkarır.
    """

    start_index = text.find(start)

    if start_index < 0:

        return ""

    section = text[
        start_index + len(start):
    ]

    end_index = len(section)

    for marker in end_markers:

        index = section.find(
            marker
        )

        if index >= 0:

            end_index = min(
                end_index,
                index,
            )

    return section[:end_index]


# =========================================================
# 1X2
# =========================================================

def _parse_1x2(
    text: str,
) -> dict[str, float] | None:
    """
    Maç Sonucu:

        1
        X
        2

    değerlerini çıkarır.
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
        rf"1\s+({_FLOAT})"
        rf"\s+X\s+({_FLOAT})"
        rf"\s+2\s+({_FLOAT})",
        section,
    )

    if not match:

        return None

    return {
        "HOME": _validate_odd(
            match.group(1)
        ),
        "DRAW": _validate_odd(
            match.group(2)
        ),
        "AWAY": _validate_odd(
            match.group(3)
        ),
    }


# =========================================================
# TOTAL GOALS
# =========================================================

def _parse_total_goals(
    text: str,
) -> dict[str, dict[str, float]]:
    """
    Toplam Goller marketlerini çıkarır.
    """

    section = _section(
        text,
        "Toplam Goller\n",
        (
            "Karşılıklı Gol Olur",
            "Beraberlikte İade",
        ),
    )

    markets: dict[
        str,
        dict[str, float],
    ] = {}

    for line in section.splitlines():

        match = re.search(
            rf"Üst\s+({_FLOAT})"
            rf"\s+({_FLOAT})"
            rf"\s+Alt\s+({_FLOAT})"
            rf"\s+({_FLOAT})",
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

        markets[
            f"TOTAL_GOALS_{threshold}"
        ] = {
            "OVER": _validate_odd(
                over
            ),
            "UNDER": _validate_odd(
                under
            ),
        }

    return markets


# =========================================================
# BTTS
# =========================================================

def _parse_btts(
    text: str,
) -> dict[str, float] | None:
    """
    Karşılıklı Gol Olur marketini çıkarır.
    """

    section = _section(
        text,
        "Karşılıklı Gol Olur\n",
        (
            "Karşılıklı Gol Olur veya "
            "2.5 Üst Gol Olur",
        ),
    )

    match = re.search(
        rf"Evet\s+({_FLOAT})"
        rf"\s+Hayır\s+({_FLOAT})",
        section,
    )

    if not match:

        return None

    return {
        "YES": _validate_odd(
            match.group(1)
        ),
        "NO": _validate_odd(
            match.group(2)
        ),
    }


# =========================================================
# TOTAL CORNERS
# =========================================================

def _parse_total_corners(
    text: str,
) -> dict[str, dict[str, float]]:
    """
    Toplam Korner marketlerini çıkarır.
    """

    section = _section(
        text,
        "Toplam Kornerler\n",
        (
            "Toplam Kornerler 3-Yönlü",
            "1. Yarı - Toplam Kornerler",
        ),
    )

    markets: dict[
        str,
        dict[str, float],
    ] = {}

    for line in section.splitlines():

        match = re.search(
            rf"Üst\s+({_FLOAT})"
            rf"\s+({_FLOAT})"
            rf"\s+Alt\s+({_FLOAT})"
            rf"\s+({_FLOAT})",
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

        markets[
            f"TOTAL_CORNERS_{threshold}"
        ] = {
            "OVER": _validate_odd(
                over
            ),
            "UNDER": _validate_odd(
                under
            ),
        }

    return markets


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_odds_pdf_text(
    pdf_path: str | Path,
) -> str:
    """
    Odds PDF'den ham text çıkarır.
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

            pages.append(
                page_text
            )

    text = "\n".join(
        pages
    )

    if not text.strip():

        raise ValueError(
            "Odds PDF metni boş."
        )

    return text.replace(
        "\r",
        "\n",
    )


# =========================================================
# TEXT → ODDS DATA
# =========================================================

def parse_odds_pdf_text(
    text: str,
) -> OddsData:
    """
    Ham PDF text'ini OddsData'ya dönüştürür.
    """

    if not isinstance(
        text,
        str,
    ):

        raise TypeError(
            "text string olmalıdır."
        )

    match = _extract_match_info(
        text
    )

    markets: dict[
        str,
        dict[str, float],
    ] = {}

    # -----------------------------------------------------
    # 1X2
    # -----------------------------------------------------

    match_result = _parse_1x2(
        text
    )

    if match_result is not None:

        markets["1X2"] = (
            match_result
        )

    # -----------------------------------------------------
    # TOTAL GOALS
    # -----------------------------------------------------

    markets.update(
        _parse_total_goals(
            text
        )
    )

    # -----------------------------------------------------
    # BTTS
    # -----------------------------------------------------

    btts = _parse_btts(
        text
    )

    if btts is not None:

        markets["BTTS"] = btts

    # -----------------------------------------------------
    # TOTAL CORNERS
    # -----------------------------------------------------

    markets.update(
        _parse_total_corners(
            text
        )
    )

    if not markets:

        raise ValueError(
            "Odds PDF içinde desteklenen "
            "market bulunamadı."
        )

    return OddsData(
        match=match,
        markets=markets,
        raw_text=text,
        source_metadata={
            "source": "OddsPDF",
            "parser": (
                ODDS_PDF_READER_VERSION
            ),
        },
    )


# =========================================================
# PDF → ODDS DATA
# =========================================================

def parse_odds_pdf(
    pdf_path: str | Path,
) -> OddsData:
    """
    Gerçek Odds PDF'sini okuyup OddsData üretir.
    """

    text = extract_odds_pdf_text(
        pdf_path
    )

    return parse_odds_pdf_text(
        text
    )


# =========================================================
# MARKET ACCESS
# =========================================================

def odds_data_to_market(
    data: OddsData,
    market: str,
) -> dict[str, float]:
    """
    OddsData içinden tek bir market çıkarır.
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
            f"Odds market bulunamadı: "
            f"{market}"
        )

    return dict(
        data.markets[key]
    )


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "ODDS_PDF_READER_VERSION",
    "extract_odds_pdf_text",
    "parse_odds_pdf_text",
    "parse_odds_pdf",
    "odds_data_to_market",
]
