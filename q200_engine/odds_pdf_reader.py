"""
Q200 Engine - Odds PDF Reader

Q200 V3.1

Gerçek Odds PDF
        ↓
OddsData

Bu katman yalnızca PDF içindeki oranları okur.

ÖNEMLİ:
- Model oluşturmaz.
- Lambda hesaplamaz.
- Poisson hesaplamaz.
- Monte Carlo çalıştırmaz.
- No-Vig hesaplamaz.
- EV hesaplamaz.
- Kelly hesaplamaz.

Odds yalnızca model LOCK sonrasında kullanılmalıdır.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from .ingestion.models import MatchInfo, OddsData


ODDS_PDF_READER_VERSION = "Q200-ODDS-PDF-READER-V1"

_FLOAT = r"\d+(?:\.\d+)?"

_MONTHS = {
    "ocak": 1,
    "şubat": 2,
    "mart": 3,
    "nisan": 4,
    "mayıs": 5,
    "haziran": 6,
    "temmuz": 7,
    "ağustos": 8,
    "eylül": 9,
    "ekim": 10,
    "kasım": 11,
    "aralık": 12,
}


def _clean_text(text: str) -> str:
    return (
        text
        .replace("\r", "\n")
        .replace("\xa0", " ")
    )


def _normalize_odd(value: str) -> float:
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


def _extract_match_info(text: str) -> MatchInfo:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    home_team: str | None = None
    away_team: str | None = None

    for line in lines[:30]:
        if " - " not in line:
            continue

        if line.startswith("Maç "):
            continue

        parts = line.split(" - ", 1)

        if len(parts) != 2:
            continue

        home = parts[0].strip()
        away = parts[1].strip()

        if not home or not away:
            continue

        home_team = home
        away_team = away
        break

    if home_team is None or away_team is None:
        raise ValueError(
            "Odds PDF maç bilgisi bulunamadı."
        )

    date: str | None = None
    time: str | None = None

    date_match = re.search(
        r"(\d{1,2})\s+"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+"
        r"(\d{4})",
        text,
    )

    if date_match:
        day, month_name, year = date_match.groups()

        month = _MONTHS.get(
            month_name.lower()
        )

        if month is not None:
            date = (
                f"{year}-"
                f"{month:02d}-"
                f"{int(day):02d}"
            )

    time_match = re.search(
        r"\b(\d{1,2}:\d{2})\b",
        text,
    )

    if time_match:
        time = time_match.group(1)

    return MatchInfo(
        home_team=home_team,
        away_team=away_team,
        date=date,
        time=time,
        source="OddsPDF",
    )


def _parse_1x2(
    text: str,
) -> dict[str, float] | None:
    marker = "Maç Sonucu\n"

    start = text.find(marker)

    if start < 0:
        return None

    section = text[start:]

    end_markers = (
        "Maç Sonucu (2 Gol Farkta Erken Ödeme)",
        "Çifte Şans",
    )

    end_positions = [
        section.find(marker)
        for marker in end_markers
        if section.find(marker) >= 0
    ]

    if end_positions:
        section = section[
            :min(end_positions)
        ]

    match = re.search(
        rf"1\s+({_FLOAT})"
        rf"\s+X\s+({_FLOAT})"
        rf"\s+2\s+({_FLOAT})",
        section,
    )

    if not match:
        return None

    home, draw, away = match.groups()

    return {
        "HOME": _normalize_odd(home),
        "DRAW": _normalize_odd(draw),
        "AWAY": _normalize_odd(away),
    }


def _parse_total_goals(
    text: str,
) -> dict[str, dict[str, float]]:
    marker = "Toplam Goller\n"

    start = text.find(marker)

    if start < 0:
        return {}

    section = text[start:]

    end_markers = (
        "Karşılıklı Gol Olur",
        "Beraberlikte İade",
        "Normal Süre Gollü Beraberlik",
    )

    end_positions = [
        section.find(marker)
        for marker in end_markers
        if section.find(marker) >= 0
    ]

    if end_positions:
        section = section[
            :min(end_positions)
        ]

    markets: dict[
        str,
        dict[str, float],
    ] = {}

    for line in section.splitlines():
        match = re.search(
            rf"Üst\s+({_FLOAT})\s+({_FLOAT})"
            rf"\s+Alt\s+({_FLOAT})\s+({_FLOAT})",
            line,
        )

        if not match:
            continue

        threshold_1, over, threshold_2, under = (
            match.groups()
        )

        if threshold_1 != threshold_2:
            continue

        markets[
            f"TOTAL_GOALS_{threshold_1}"
        ] = {
            "OVER": _normalize_odd(over),
            "UNDER": _normalize_odd(under),
        }

    return markets


def _parse_btts(
    text: str,
) -> dict[str, float] | None:
    marker = "Karşılıklı Gol Olur\n"

    start = text.find(marker)

    if start < 0:
        return None

    section = text[start:]

    end_marker = (
        "Karşılıklı Gol Olur veya "
        "2.5 Üst Gol Olur"
    )

    end = section.find(end_marker)

    if end >= 0:
        section = section[:end]

    match = re.search(
        rf"Evet\s+({_FLOAT})"
        rf"\s+Hayır\s+({_FLOAT})",
        section,
    )

    if not match:
        return None

    yes, no = match.groups()

    return {
        "YES": _normalize_odd(yes),
        "NO": _normalize_odd(no),
    }


def _parse_total_corners(
    text: str,
) -> dict[str, dict[str, float]]:
    marker = "Toplam Kornerler\n"

    start = text.find(marker)

    if start < 0:
        return {}

    section = text[start:]

    end_markers = (
        "Toplam Kornerler 3-Yönlü",
        "1. Yarı - Toplam Kornerler",
    )

    end_positions = [
        section.find(marker)
        for marker in end_markers
        if section.find(marker) >= 0
    ]

    if end_positions:
        section = section[
            :min(end_positions)
        ]

    markets: dict[
        str,
        dict[str, float],
    ] = {}

    for line in section.splitlines():
        match = re.search(
            rf"Üst\s+({_FLOAT})\s+({_FLOAT})"
            rf"\s+
