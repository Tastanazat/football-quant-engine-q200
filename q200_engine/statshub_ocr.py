"""
Q200 Engine - StatsHub OCR

Q200 V3.1

StatsHub ekran görüntülerini OCR ile okuyup zengin statistics
verisine dönüştürür.

Akış:

IMAGE
  ↓
OCR
  ↓
ROW DETECTION
  ↓
STAT LABEL MAPPING
  ↓
RAW VALUES
  ↓
DATA REVIEW

Bu modül model hesabı yapmaz ve odds kullanmaz.

OCR sonucu doğrudan Q200 modeline gönderilmez.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from .data_review import DataReview, create_review


STATSHUB_OCR_VERSION = "Q200-STATSHUB-OCR-V1"


# StatsHub ekran görüntüsündeki gerçek satır adlarını
# canonical alanlara bağlarız.
STAT_LABELS: dict[str, str] = {
    "goals": "goals",
    "corners": "corners",
    "cards": "cards",
    "crosses": "crosses",
    "big chance created": "big_chance_created",
    "big chance missed": "big_chance_missed",
    "big chance scored": "big_chance_scored",
    "expected goals (xg)": "xg",
    "expected goals": "xg",
    "shots on target": "shots_on_target",
    "shots in the box": "shots_in_box",
    "total shots": "total_shots",
    "shots outside the box": "shots_outside_box",
    "clearances": "clearances",
    "dispossessed": "dispossessed",
    "errors lead to goal": "errors_lead_to_goal",
    "errors lead to shot": "errors_lead_to_shot",
    "fouls": "fouls",
    "goalkeeper saves": "goalkeeper_saves",
    "interception won": "interceptions_won",
    "interceptions won": "interceptions_won",
    "tackles": "tackles",
    "free kicks": "free_kicks",
    "goal kicks": "goal_kicks",
    "throw ins": "throw_ins",
    "throw-ins": "throw_ins",
    "possession": "possession",
    "offsides": "offsides",
    "passes": "passes",
    "touches in opp box": "touches_in_opp_box",
    "touches in opp. box": "touches_in_opp_box",
    "red cards": "red_cards",
    "yellow cards": "yellow_cards",
}


_OCR_REPLACEMENTS = str.maketrans(
    {
        "×": "x",
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "’": "'",
    }
)


_NUMBER_RE = re.compile(
    r"(?<!\d)(\d+(?:[.,]\d+)?%?)(?!\d)"
)


class StatsHubOCRError(RuntimeError):
    """StatsHub OCR işlem hatası."""


def normalize_ocr_text(text: str) -> str:
    """OCR metnini parser için normalize eder."""

    if not isinstance(text, str):
        raise TypeError(
            "OCR text string olmalıdır."
        )

    text = text.translate(
        _OCR_REPLACEMENTS
    )

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    lines = []

    for line in text.split("\n"):

        cleaned = " ".join(
            line.split()
        )

        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)


def _normalize_label(
    label: str,
) -> str:

    label = label.strip().lower()

    label = re.sub(
        r"\s+",
        " ",
        label,
    )

    label = label.replace(
        "opp.",
        "opp box",
    )

    label = label.replace(
        "opp box box",
        "opp box",
    )

    return label


def canonical_stat_name(
    label: str,
) -> str | None:
    """StatsHub satır adını canonical alan adına çevirir."""

    normalized = _normalize_label(
        label
    )

    if normalized in STAT_LABELS:
        return STAT_LABELS[normalized]

    return None


def parse_number(
    value: str,
) -> float:
    """OCR sayı değerini float'a çevirir."""

    if not isinstance(value, str):
        raise TypeError(
            "OCR sayı değeri string olmalıdır."
        )

    cleaned = (
        value
        .strip()
        .replace(",", ".")
    )

    cleaned = cleaned.rstrip("%")

    try:
        number = float(cleaned)

    except ValueError as exc:

        raise ValueError(
            f"Geçersiz OCR sayı değeri: {value}"
        ) from exc

    if not math.isfinite(number):

        raise ValueError(
            f"OCR sayı değeri sonlu olmalıdır: {value}"
        )

    return number


def extract_numbers(
    text: str,
) -> list[float]:
    """Bir OCR satırındaki sayıları sırayla döndürür."""

    return [
        parse_number(
            match.group(1)
        )
        for match in _NUMBER_RE.finditer(text)
    ]


def _extract_label_and_numbers(
    line: str,
) -> tuple[str, list[float]]:

    matches = list(
        _NUMBER_RE.finditer(line)
    )

    if not matches:
        return line.strip(), []

    label = line[
        : matches[0].start()
    ].strip()

    numbers = [
        parse_number(
            match.group(1)
        )
        for match in matches
    ]

    return label, numbers


def parse_statshub_text(
    text: str,
    *,
    value_column: str = "avg",
) -> dict[str, Any]:
    """
    OCR'dan elde edilmiş satır bazlı StatsHub metnini parse eder.

    StatsHub tablosunda tipik yapı:

        Goals  3.05  1.70  1.35
        Corners 9.15 4.30 4.85

    Varsayılan olarak ilk sayı (AVG) alınır.

    value_column seçenekleri:

        avg
        for
        agt

    Bu fonksiyon ilk üç tablo kolonunu yorumlar:

        AVG
        FOR
        AGT

    Maç geçmişindeki hücreler model girdisi olarak kullanılmaz.
    """

    if value_column not in {
        "avg",
        "for",
        "agt",
    }:
        raise ValueError(
            "value_column avg, for veya agt olmalıdır."
        )

    normalized_text = normalize_ocr_text(
        text
    )

    result: dict[str, Any] = {}

    index = {
        "avg": 0,
        "for": 1,
        "agt": 2,
    }[value_column]

    for line in normalized_text.split("\n"):

        label, numbers = (
            _extract_label_and_numbers(
                line
            )
        )

        if not numbers:
            continue

        canonical = canonical_stat_name(
            label
        )

        if canonical is None:
            continue

        if len(numbers) <= index:
            continue

        result[canonical] = numbers[index]

    return result


def parse_statshub_table_text(
    text: str,
) -> dict[str, dict[str, float]]:
    """
    StatsHub metnindeki AVG/FOR/AGT değerlerini birlikte döndürür.

    Örnek:

        {
            "goals": {
                "avg": 3.05,
                "for": 1.70,
                "agt": 1.35
            }
        }
    """

    normalized_text = normalize_ocr_text(
        text
    )

    result: dict[
        str,
        dict[str, float],
    ] = {}

    for line in normalized_text.split("\n"):

        label, numbers = (
            _extract_label_and_numbers(
                line
            )
        )

        canonical = canonical_stat_name(
            label
        )

        if canonical is None:
            continue

        if len(numbers) < 1:
            continue

        columns: dict[str, float] = {
            "avg": numbers[0],
        }

        if len(numbers) >= 2:
            columns["for"] = numbers[1]

        if len(numbers) >= 3:
            columns["agt"] = numbers[2]

        result[canonical] = columns

    return result


def ocr_image_to_text(
    image_path: str | Path,
    *,
    ocr_engine: Callable[[Any], str] | None = None,
) -> str:
    """
    Görüntüyü OCR ile metne çevirir.

    Test ve alternatif OCR motorları için
    ocr_engine inject edilebilir.

    Varsayılan motor pytesseract'tır.

    Tesseract sistemde kurulu değilse açık
    bir hata döndürür.
    """

    path = Path(image_path)

    if not path.exists():

        raise FileNotFoundError(
            f"StatsHub görüntüsü bulunamadı: {path}"
        )

    if not path.is_file():

        raise ValueError(
            f"StatsHub görüntü yolu dosya olmalıdır: {path}"
        )

    try:

        from PIL import Image

    except ImportError as exc:

        raise StatsHubOCRError(
            "OCR için Pillow gereklidir."
        ) from exc

    image = Image.open(path)

    try:

        if ocr_engine is not None:
            return ocr_engine(image)

        try:

            import pytesseract

        except ImportError as exc:

            raise StatsHubOCRError(
                "OCR için pytesseract gereklidir."
            ) from exc

        try:

            return pytesseract.image_to_string(
                image
            )

        except Exception as exc:

            raise StatsHubOCRError(
                "Tesseract OCR çalıştırılamadı. "
                "Tesseract kurulumu ve PATH ayarını "
                "kontrol edin."
            ) from exc

    finally:

        image.close()


def create_statshub_review(
    image_path: str | Path,
    *,
    review_id: str | None = None,
    value_column: str = "avg",
    confidence: Mapping[str, float] | None = None,
    metadata: Mapping[str, Any] | None = None,
    ocr_text: str | None = None,
    ocr_engine: Callable[[Any], str] | None = None,
) -> DataReview:
    """
    StatsHub görüntüsünü:

        OCR
        ↓
        Parser
        ↓
        DataReview

    akışına bağlar.

    OCR sonucu doğrudan modele gönderilmez.

    Oluşturulan review başlangıçta
    APPROVED değildir.
    """

    path = Path(image_path)

    if ocr_text is None:

        ocr_text = ocr_image_to_text(
            path,
            ocr_engine=ocr_engine,
        )

    values = parse_statshub_text(
        ocr_text,
        value_column=value_column,
    )

    if not values:

        raise StatsHubOCRError(
            "StatsHub OCR sonucunda tanınan "
            "statistics alanı bulunamadı."
        )

    if review_id is None:

        review_id = (
            f"statshub:{path.name}"
        )

    review_metadata = dict(
        metadata or {}
    )

    review_metadata.update(
        {
            "ocr_version": STATSHUB_OCR_VERSION,
            "value_column": value_column,
            "ocr_text": normalize_ocr_text(
                ocr_text
            ),
        }
    )

    return create_review(
        review_id=review_id,
        source_type="OCR",
        source_file=str(path),
        values=values,
        confidence=dict(
            confidence or {}
        ),
        metadata=review_metadata,
    )
