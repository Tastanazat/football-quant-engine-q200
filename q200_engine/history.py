"""
Q200 Engine - Analysis History

Q200 V3.1

Q200 analiz raporlarını kalıcı SQLite veritabanında saklar.

Bu katman:
- Model hesabı yapmaz.
- Odds hesabı yapmaz.
- Selection değiştirmez.
- Kayıtlı raporu değiştirmez.
- Sadece AnalysisResult -> report -> SQLite geçmişi sağlar.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .report import build_report


HISTORY_SCHEMA_VERSION = "Q200-HISTORY-V1"


def _validate_text(
    value: Any,
    name: str,
) -> str:

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            f"{name} string olmalıdır."
        )

    result = value.strip()

    if not result:
        raise ValueError(
            f"{name} boş olamaz."
        )

    return result


def _utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


class AnalysisHistory:
    """
    Q200 analiz geçmişi için SQLite repository.
    """

    def __init__(
        self,
        path: str | Path,
    ):

        self.path = Path(path)

        if (
            self.path.exists()
            and self.path.is_dir()
        ):
            raise ValueError(
                "History path bir dosya olmalıdır: "
                f"{self.path}"
            )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialize(
        self,
    ) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    report_version TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    report_json TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def save(
        self,
        result,
        match_id: str,
    ) -> int:
        """
        AnalysisResult'ı geçmişe kaydeder
        ve kayıt ID'sini döndürür.
        """

        match_id = _validate_text(
            match_id,
            "match_id",
        )

        report = build_report(
            result
        )

        report_json = json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=False,
        )

        created_at = _utc_now()

        with self._connect() as connection:

            cursor = connection.execute(
                """
                INSERT INTO analysis_history (
                    match_id,
                    created_at,
                    report_version,
                    model_version,
                    report_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    created_at,
                    report["report_version"],
                    report["model_version"],
                    report_json,
                ),
            )

            connection.commit()

            return int(
                cursor.lastrowid
            )

    def get(
        self,
        record_id: int,
    ) -> dict[str, Any] | None:
        """
        ID ile tek geçmiş kaydını getirir.
        """

        if not isinstance(
            record_id,
            int,
        ):
            raise TypeError(
                "record_id integer olmalıdır."
            )

        if record_id <= 0:
            raise ValueError(
                "record_id pozitif olmalıdır."
            )

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT
                    id,
                    match_id,
                    created_at,
                    report_version,
                    model_version,
                    report_json
                FROM analysis_history
                WHERE id = ?
                """,
                (
                    record_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "match_id": row["match_id"],
            "created_at": row["created_at"],
            "report_version": row["report_version"],
            "model_version": row["model_version"],
            "report": json.loads(
                row["report_json"]
            ),
        }

    def list(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        En yeni analizleri listeler.
        """

        if not isinstance(
            limit,
            int,
        ):
            raise TypeError(
                "limit integer olmalıdır."
            )

        if limit <= 0:
            raise ValueError(
                "limit pozitif olmalıdır."
            )

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    id,
                    match_id,
                    created_at,
                    report_version,
                    model_version
                FROM analysis_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    limit,
                ),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "match_id": row["match_id"],
                "created_at": row["created_at"],
                "report_version": row["report_version"],
                "model_version": row["model_version"],
            }
            for row in rows
        ]

    def count(
        self,
    ) -> int:
        """
        Toplam kayıt sayısını döndürür.
        """

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM analysis_history
                """
            ).fetchone()

        return int(
            row["count"]
        )

    def delete(
        self,
        record_id: int,
    ) -> bool:
        """
        Bir geçmiş kaydını siler.

        Başarılıysa True döner.
        """

        if not isinstance(
            record_id,
            int,
        ):
            raise TypeError(
                "record_id integer olmalıdır."
            )

        if record_id <= 0:
            raise ValueError(
                "record_id pozitif olmalıdır."
            )

        with self._connect() as connection:

            cursor = connection.execute(
                """
                DELETE FROM analysis_history
                WHERE id = ?
                """,
                (
                    record_id,
                ),
            )

            connection.commit()

            return (
                cursor.rowcount == 1
            )
