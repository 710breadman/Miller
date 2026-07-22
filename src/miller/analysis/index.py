"""SQLite-backed searchable page-understanding index."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import PageAnalysis


class AnalysisIndex:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS page_analysis (
                    page_id TEXT PRIMARY KEY,
                    source_locator TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    search_text TEXT NOT NULL,
                    record_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_page_analysis_locator
                    ON page_analysis(source_locator);
                """
            )

    def upsert(self, record: PageAnalysis) -> None:
        search_text = self._search_text(record)
        payload = record.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO page_analysis(
                    page_id, source_locator, source_sha256, search_text, record_json
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(page_id) DO UPDATE SET
                    source_locator=excluded.source_locator,
                    source_sha256=excluded.source_sha256,
                    search_text=excluded.search_text,
                    record_json=excluded.record_json
                """,
                (
                    record.page_id,
                    record.source_locator,
                    record.source_sha256,
                    search_text,
                    payload,
                ),
            )

    def get(self, page_id: str) -> PageAnalysis:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM page_analysis WHERE page_id=?", (page_id,)
            ).fetchone()
        if row is None:
            raise KeyError(page_id)
        return PageAnalysis.model_validate_json(row["record_json"])

    def search(
        self,
        query: str,
        *,
        character: str | None = None,
        mood: str | None = None,
        limit: int = 20,
    ) -> list[PageAnalysis]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        terms = [term.casefold() for term in query.split() if term.strip()]
        if character:
            terms.append(character.casefold())
        if mood:
            terms.append(mood.casefold())
        clauses = ["instr(lower(search_text), ?) > 0" for _ in terms]
        sql = "SELECT record_json FROM page_analysis"
        parameters: list[object] = []
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
            parameters.extend(terms)
        sql += " ORDER BY page_id LIMIT ?"
        parameters.append(limit)
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [PageAnalysis.model_validate_json(row["record_json"]) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM page_analysis").fetchone()
        assert row is not None
        return int(row["count"])

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @staticmethod
    def _search_text(record: PageAnalysis) -> str:
        parts = [
            record.source_locator,
            record.description.summary,
            *record.description.characters,
            *record.description.actions,
            *record.description.moods,
            *record.description.visual_tags,
        ]
        if record.ocr is not None:
            parts.extend(span.text for span in record.ocr.spans)
        return "\n".join(parts)
