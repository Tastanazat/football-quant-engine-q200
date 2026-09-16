"""
Q200 Engine - Odds Reader

Q200 V3.1

CSV / XLSX dosyalarından Odds verisini okur.

Kanonik Odds formatı:

    outcome,odds

Örnek:

    HOME,2.10
    DRAW,3.40
    AWAY,3.80

Bu katman:

- Model hesabı yapmaz.
- Statistics verisi kullanmaz.
- Lambda hesaplamaz.
- Model olasılığı üretmez.
- Vig / No-Vig hesabı yapmaz.
- EV hesaplamaz.
- Kelly hesaplamaz.

Sadece Odds dosyasını güvenli şekilde okuyup
Q200Pipeline'ın beklediği dictionary yapısına dönüştürür.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
}

REQUIRED_HEADERS = {
    "outcome",
    "odds",
}


def _normalize_header(
    header: Any,
) -> str:
    """
    Sütun adını normalize eder.
    """

    if not isinstance(header, str):
        raise TypeError(
            "Odds sütun isimleri string olmalıdır."
        )

    normalized = (
        header
        .strip()
        .lower()
    )

    if not normalized:
        raise ValueError(
            "Boş Odds sütun adı kullanılamaz."
        )

    if normalized not in REQUIRED_HEADERS:
        raise ValueError(
            f"Bilinmeyen Odds sütunu: {normalized}"
        )

    return normalized


def _normalize_outcome(
    value: Any,
) -> str:
    """
    Market/outcome değerini normalize eder.
    """

    if value is None:
        raise ValueError(
            "Odds outcome boş olamaz."
        )

    outcome = str(value).strip().upper()

    if not outcome:
        raise ValueError(
            "Odds outcome boş olamaz."
        )

    return outcome


def _normalize_odds(
    value: Any,
) -> float:
    """
    Odds değerini güvenli float'a dönüştürür.
    """

    if isinstance(value, bool):
        raise ValueError(
            "Odds boolean olamaz."
        )

    try:
        odd = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Geçersiz Odds değeri: {value}"
        ) from exc

    if not math.isfinite(odd):
        raise ValueError(
            f"Odds sonlu bir sayı olmalıdır: {value}"
        )

    if odd <= 1.0:
        raise ValueError(
            f"Odds 1.00'dan büyük olmalıdır: {value}"
        )

    return odd


def _validate_headers(
    raw_headers: list[Any],
) -> list[str]:
    """
    Header'ları normalize eder ve doğrular.
    """

    headers = [
        _normalize_header(header)
        for header in raw_headers
    ]

    if len(headers) != len(set(headers)):
        raise ValueError(
            "Odds dosyasında tekrar eden sütun adı var."
        )

    missing = REQUIRED_HEADERS - set(headers)

    if missing:
        raise ValueError(
            "Eksik Odds sütunu: "
            + ", ".join(sorted(missing))
        )

    return headers


def _append_row(
    rows: list[dict[str, float]],
    row: dict[str, Any],
) -> None:
    """
    Tek bir Odds satırını doğrular ve listeye ekler.
    """

    outcome = _normalize_outcome(
        row.get("outcome")
    )

    odd = _normalize_odds(
        row.get("odds")
    )

    rows.append(
        {
            "outcome": outcome,
            "odds": odd,
        }
    )


def read_odds_csv(
    path: str | Path,
) -> list[dict[str, float]]:
    """
    CSV Odds dosyasını okur.

    Beklenen format:

        outcome,odds
        HOME,2.10
        DRAW,3.40
        AWAY,3.80
    """

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Odds dosyası bulunamadı: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Odds path bir dosya olmalıdır: {file_path}"
        )

    rows: list[dict[str, float]] = []

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                "CSV Odds dosyasında sütun başlığı bulunamadı."
            )

        headers = _validate_headers(
            list(reader.fieldnames)
        )

        for raw_row in reader:

            if not raw_row:
                continue

            row: dict[str, Any] = {}

            for header in headers:
                row[header] = raw_row.get(header)

            if all(
                value is None
                or (
                    isinstance(value, str)
                    and not value.strip()
                )
                for value in row.values()
            ):
                continue

            _append_row(
                rows,
                row,
            )

    if not rows:
        raise ValueError(
            "CSV Odds dosyasında veri satırı bulunamadı."
        )

    return rows


def read_odds_xlsx(
    path: str | Path,
) -> list[dict[str, float]]:
    """
    XLSX Odds dosyasını okur.

    İlk worksheet ve ilk satır header olarak kullanılır.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Odds dosyası bulunamadı: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Odds path bir dosya olmalıdır: {file_path}"
        )

    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ImportError(
            "XLSX okumak için openpyxl gereklidir."
        ) from exc

    workbook = load_workbook(
        filename=file_path,
        read_only=True,
        data_only=True,
    )

    try:
        worksheet = workbook.active

        rows_iterator = worksheet.iter_rows(
            values_only=True
        )

        try:
            raw_headers = next(
                rows_iterator
            )
        except StopIteration as exc:
            raise ValueError(
                "XLSX Odds dosyası boş."
            ) from exc

        headers = _validate_headers(
            list(raw_headers)
        )

        rows: list[dict[str, float]] = []

        for raw_row in rows_iterator:

            row: dict[str, Any] = {}

            for index, header in enumerate(headers):

                value = (
                    raw_row[index]
                    if index < len(raw_row)
                    else None
                )

                row[header] = value

            if all(
                value is None
                or (
                    isinstance(value, str)
                    and not value.strip()
                )
                for value in row.values()
            ):
                continue

            _append_row(
                rows,
                row,
            )

        if not rows:
            raise ValueError(
                "XLSX Odds dosyasında veri satırı bulunamadı."
            )

        return rows

    finally:
        workbook.close()


def read_odds_file(
    path: str | Path,
) -> list[dict[str, float]]:
    """
    CSV veya XLSX Odds dosyasını okur.
    """

    file_path = Path(path)

    extension = file_path.suffix.lower()

    if extension == ".csv":
        return read_odds_csv(
            file_path
        )

    if extension == ".xlsx":
        return read_odds_xlsx(
            file_path
        )

    raise ValueError(
        "Desteklenmeyen Odds dosya tipi: "
        f"{extension or '[uzantı yok]'}"
    )


def read_odds_dict(
    path: str | Path,
) -> dict[str, float]:
    """
    Odds dosyasını Q200Pipeline'ın beklediği
    dictionary formatına dönüştürür.

    Örnek çıktı:

        {
            "HOME": 2.10,
            "DRAW": 3.40,
            "AWAY": 3.80,
        }
    """

    rows = read_odds_file(
        path
    )

    odds: dict[str, float] = {}

    for row in rows:

        outcome = row["outcome"]
        odd = row["odds"]

        if outcome in odds:
            raise ValueError(
                "Odds dosyasında tekrar eden outcome: "
                f"{outcome}"
            )

        odds[outcome] = odd

    if not odds:
        raise ValueError(
            "Odds dictionary boş olamaz."
        )

    return odds
