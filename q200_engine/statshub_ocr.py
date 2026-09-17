"""
Q200 Engine - StatsHub OCR

Q200 V3.1

StatsHub fixture ekran görüntülerinden görünen istatistik satırlarını
OCR ile okuyup Data Review katmanına hazırlar.

Önemli tasarım kararı:
- OCR sonucu model katmanına doğrudan gitmez.
- AVG / FOR / AGT değerleri ayrı tutulur.
- Maç geçmişindeki sütunlar yanlışlıkla AVG/FOR/AGT yerine kullanılmaz.
- Ham OCR metni DataReview.metadata içinde korunur.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from .data_review import DataReview, create_review


STATSHUB_OCR_VERSION = "Q200-STATSHUB-OCR-V1"


STAT_LABELS: dict[str, str] = {
    "goals": "goals",
    "corners": "corners",
    "comers": "corners",
    "cards": "cards",
    "crosses": "crosses",
    "big chance created": "big_chance_created",
    "big chance missed": "big_chance_missed",
    "big chance scored": "big_chance_scored",
    "expected goals (xg)": "xg",
    "expected goals xg": "xg",
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


_NUMBER_RE = re.compile(
    r"(?<!\d)(\d+(?:[.,]\d+)?%?)(?!\d)"
)


def normalize_ocr_text(text: str) -> str:
    """OCR metnini satır bazında normalize eder."""

    if not isinstance(text, str):
        raise TypeError(
            "OCR text string olmalıdır."
        )

    text = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("–", "-")
        .replace("—", "-")
        .replace("×", "x")
    )

    return "\n".join(
        " ".join(line.split())
        for line in text.split("\n")
        if line.strip()
    )


def _normalize_label(label: str) -> str:
    label = label.strip().lower()
    label = re.sub(r"\s+", " ", label)
    label = label.replace("opp.", "opp box")
    label = label.replace("opp box box", "opp box")
    return label


def canonical_stat_name(
    label: str,
) -> str | None:
    """StatsHub satır adını canonical alana çevirir."""

    return STAT_LABELS.get(
        _normalize_label(label)
    )


def parse_number(
    value: str,
) -> float:
    """OCR sayı metnini sonlu float değerine çevirir."""

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
    """Bir satırdaki sayıları soldan sağa çıkarır."""

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
        :matches[0].start()
    ].strip()

    numbers = [
        parse_number(
            match.group(1)
        )
        for match in matches
    ]

    return label, numbers


def parse_statshub_table_text(
    text: str,
) -> dict[str, dict[str, float]]:
    """
    StatsHub OCR metnindeki özet tabloyu parse eder.

    İlk üç özet sütun:

        AVG | FOR | AGT

    ayrı ayrı tutulur.

    Sonraki maç geçmişi sütunları alınmaz.
    """

    normalized = normalize_ocr_text(text)

    result: dict[
        str,
        dict[str, float],
    ] = {}

    for line in normalized.split("\n"):

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

        if not numbers:
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


def flatten_statshub_summary(
    table: Mapping[
        str,
        Mapping[str, float],
    ],
    *,
    include_columns: tuple[str, ...] = (
        "avg",
        "for",
        "agt",
    ),
) -> dict[str, float]:
    """
    AVG/FOR/AGT tablosunu DataReview için düz dictionary'ye çevirir.

    Örnek:

        goals_avg
        goals_for
        goals_agt

    Böylece aynı istatistiğin farklı sütunları karışmaz.
    """

    allowed = {
        "avg",
        "for",
        "agt",
    }

    for column in include_columns:

        if column not in allowed:
            raise ValueError(
                "include_columns yalnızca "
                "avg, for, agt içerebilir."
            )

    result: dict[str, float] = {}

    for field_name, values in table.items():

        for column in include_columns:

            if column in values:

                result[
                    f"{field_name}_{column}"
                ] = float(
                    values[column]
                )

    return result


def parse_statshub_text(
    text: str,
    *,
    value_column: str = "avg",
) -> dict[str, float]:
    """Tek bir özet sütununu canonical dictionary olarak döndürür."""

    if value_column not in {
        "avg",
        "for",
        "agt",
    }:
        raise ValueError(
            "value_column avg, for veya agt olmalıdır."
        )

    table = parse_statshub_table_text(
        text
    )

    return {
        field_name: values[value_column]
        for field_name, values in table.items()
        if value_column in values
    }


def _preprocess_image(
    image: Any,
) -> Any:
    """
    OCR öncesi StatsHub mobil ekran görüntüsü için
    hafif görüntü iyileştirmesi yapar.
    """

    from PIL import ImageEnhance
    from PIL import ImageOps

    gray = ImageOps.grayscale(
        image
    )

    width, height = gray.size

    gray = gray.resize(
        (
            width * 2,
            height * 2,
        )
    )

    gray = ImageOps.autocontrast(
        gray
    )

    gray = ImageEnhance.Contrast(
        gray
    ).enhance(2.5)

    return gray


def ocr_image_to_text(
    image_path: str | Path,
    *,
    ocr_engine: Callable[
        [Any],
        str,
    ] | None = None,
) -> str:
    """
    Görüntüyü OCR ile metne çevirir.

    Test/alternatif OCR motoru için
    ocr_engine dışarıdan verilebilir.

    Varsayılan:

        Pillow
        +
        pytesseract
        +
        Tesseract
    """

    path = Path(
        image_path
    )

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

        raise RuntimeError(
            "StatsHub OCR için Pillow gereklidir."
        ) from exc

    image = Image.open(
        path
    )

    try:

        if ocr_engine is not None:
            return ocr_engine(
                image
            )

        try:

            import pytesseract

        except ImportError as exc:

            raise RuntimeError(
                "StatsHub OCR için pytesseract gereklidir."
            ) from exc

        processed = _preprocess_image(
            image
        )

        try:

            return pytesseract.image_to_string(
                processed,
                config="--psm 4",
            )

        except Exception as exc:

            raise RuntimeError(
                "Tesseract OCR çalıştırılamadı. "
                "Tesseract kurulumu/PATH ayarını "
                "kontrol edin."
            ) from exc

        finally:

            processed.close()

    finally:

        image.close()


def create_statshub_review(
    image_path: str | Path,
    *,
    review_id: str | None = None,
    confidence: Mapping[
        str,
        float,
    ] | None = None,
    metadata: Mapping[
        str,
        Any,
    ] | None = None,
    ocr_text: str | None = None,
    ocr_engine: Callable[
        [Any],
        str,
    ] | None = None,
    include_columns: tuple[
        str,
        ...,
    ] = (
        "avg",
        "for",
        "agt",
    ),
) -> DataReview:
    """
    StatsHub:

        IMAGE
          ↓
        OCR
          ↓
        PARSER
          ↓
        DATA REVIEW

    akışını oluşturur.

    Review başlangıçta onaysızdır.
    """

    path = Path(
        image_path
    )

    if ocr_text is None:

        ocr_text = ocr_image_to_text(
            path,
            ocr_engine=ocr_engine,
        )

    table = parse_statshub_table_text(
        ocr_text
    )

    values = flatten_statshub_summary(
        table,
        include_columns=include_columns,
    )

    if not values:

        raise RuntimeError(
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
            "ocr_version":
                STATSHUB_OCR_VERSION,
            "ocr_text":
                normalize_ocr_text(
                    ocr_text
                ),
            "columns":
                list(include_columns),
            "parsed_table":
                table,
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
