"""SQLite Registry for Kaggle AutoResearch Orchestrator."""

import datetime
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from orch.logging_util import get_logger

logger = get_logger("orch.registry")


class Registry:
    """Manages the SQLite database for competitions, submissions, notebooks, experiments, and budgets."""

    def __init__(self, db_path: str = "registry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Initializes database schema if not present."""
        conn = self._get_connection()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS competitions (
                    slug TEXT PRIMARY KEY,
                    id INTEGER,
                    title TEXT,
                    url TEXT,
                    deadline TEXT,
                    category TEXT,
                    reward TEXT,
                    evaluation_metric TEXT,
                    direction TEXT,
                    kind TEXT,
                    status TEXT,
                    is_kernels_submissions_only INTEGER,
                    max_daily_submissions INTEGER,
                    my_best_public_score REAL,
                    my_best_submission_ref INTEGER,
                    discovered_at TEXT,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    ref INTEGER PRIMARY KEY,
                    competition_slug TEXT,
                    file_name TEXT,
                    date TEXT,
                    description TEXT,
                    status TEXT,
                    public_score REAL,
                    private_score REAL,
                    is_baseline INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY(competition_slug) REFERENCES competitions(slug)
                );

                CREATE TABLE IF NOT EXISTS notebooks (
                    ref TEXT PRIMARY KEY,
                    competition_slug TEXT,
                    title TEXT,
                    author TEXT,
                    slug TEXT,
                    total_votes INTEGER,
                    best_score REAL,
                    url TEXT,
                    techniques_extracted TEXT,
                    license TEXT,
                    is_reproducible INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY(competition_slug) REFERENCES competitions(slug)
                );

                CREATE TABLE IF NOT EXISTS experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competition_slug TEXT,
                    commit_hash TEXT,
                    cv_mean REAL,
                    cv_std REAL,
                    runtime_sec REAL,
                    memory_mb REAL,
                    status TEXT,
                    description TEXT,
                    created_at TEXT,
                    FOREIGN KEY(competition_slug) REFERENCES competitions(slug)
                );

                CREATE TABLE IF NOT EXISTS budgets (
                    competition_slug TEXT PRIMARY KEY,
                    daily_submission_cap INTEGER,
                    submissions_today INTEGER DEFAULT 0,
                    last_submission_date TEXT,
                    timeout_seconds INTEGER,
                    memory_limit_mb INTEGER,
                    FOREIGN KEY(competition_slug) REFERENCES competitions(slug)
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def upsert_competition(self, data: Dict[str, Any]) -> None:
        """Inserts or updates a competition record."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            existing = conn.execute("SELECT slug, discovered_at FROM competitions WHERE slug = ?", (data["slug"],)).fetchone()
            discovered_at = existing["discovered_at"] if existing else now
            conn.execute(
                """
                INSERT INTO competitions (
                    slug, id, title, url, deadline, category, reward, evaluation_metric,
                    direction, kind, status, is_kernels_submissions_only, max_daily_submissions,
                    my_best_public_score, my_best_submission_ref, discovered_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    id = excluded.id,
                    title = excluded.title,
                    url = excluded.url,
                    deadline = excluded.deadline,
                    category = excluded.category,
                    reward = excluded.reward,
                    evaluation_metric = excluded.evaluation_metric,
                    direction = excluded.direction,
                    kind = excluded.kind,
                    status = excluded.status,
                    is_kernels_submissions_only = excluded.is_kernels_submissions_only,
                    max_daily_submissions = excluded.max_daily_submissions,
                    my_best_public_score = excluded.my_best_public_score,
                    my_best_submission_ref = excluded.my_best_submission_ref,
                    updated_at = excluded.updated_at;
                """,
                (
                    data["slug"],
                    data.get("id"),
                    data.get("title"),
                    data.get("url"),
                    data.get("deadline"),
                    data.get("category"),
                    data.get("reward"),
                    data.get("evaluation_metric"),
                    data.get("direction", "maximize"),
                    data.get("kind", "other"),
                    data.get("status", "report_only"),
                    1 if data.get("is_kernels_submissions_only") else 0,
                    data.get("max_daily_submissions", 5),
                    data.get("my_best_public_score"),
                    data.get("my_best_submission_ref"),
                    discovered_at,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_competition(self, slug: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM competitions WHERE slug = ?", (slug,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_competitions(self, kind: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM competitions WHERE 1=1"
        params: List[Any] = []
        if kind:
            query += " AND kind = ?"
            params.append(kind)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY deadline ASC"

        conn = self._get_connection()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_submission(self, data: Dict[str, Any]) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO submissions (
                    ref, competition_slug, file_name, date, description, status,
                    public_score, private_score, is_baseline, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ref) DO UPDATE SET
                    description = excluded.description,
                    status = excluded.status,
                    public_score = excluded.public_score,
                    private_score = excluded.private_score,
                    is_baseline = excluded.is_baseline;
                """,
                (
                    data["ref"],
                    data["competition_slug"],
                    data.get("file_name", ""),
                    data.get("date", ""),
                    data.get("description", ""),
                    data.get("status", ""),
                    data.get("public_score"),
                    data.get("private_score"),
                    1 if data.get("is_baseline") else 0,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_submissions(self, competition_slug: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM submissions WHERE competition_slug = ? ORDER BY date DESC",
                (competition_slug,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_notebook(self, data: Dict[str, Any]) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO notebooks (
                    ref, competition_slug, title, author, slug, total_votes,
                    best_score, url, techniques_extracted, license, is_reproducible, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ref) DO UPDATE SET
                    total_votes = excluded.total_votes,
                    best_score = excluded.best_score,
                    techniques_extracted = excluded.techniques_extracted,
                    license = excluded.license,
                    is_reproducible = excluded.is_reproducible;
                """,
                (
                    data["ref"],
                    data["competition_slug"],
                    data.get("title", ""),
                    data.get("author", ""),
                    data.get("slug", ""),
                    data.get("total_votes", 0),
                    data.get("best_score"),
                    data.get("url", ""),
                    data.get("techniques_extracted", ""),
                    data.get("license", "Unknown"),
                    1 if data.get("is_reproducible") else 0,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_notebooks(self, competition_slug: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM notebooks WHERE competition_slug = ? ORDER BY total_votes DESC",
                (competition_slug,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def record_experiment(self, data: Dict[str, Any]) -> int:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO experiments (
                    competition_slug, commit_hash, cv_mean, cv_std, runtime_sec,
                    memory_mb, status, description, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["competition_slug"],
                    data.get("commit_hash", ""),
                    data.get("cv_mean"),
                    data.get("cv_std"),
                    data.get("runtime_sec", 0.0),
                    data.get("memory_mb", 0.0),
                    data.get("status", "discard"),
                    data.get("description", ""),
                    now,
                ),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def list_experiments(self, competition_slug: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM experiments WHERE competition_slug = ? ORDER BY id ASC",
                (competition_slug,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def set_budget(self, competition_slug: str, cap: int, timeout_sec: int, mem_mb: int) -> None:
        today = datetime.date.today().isoformat()
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO budgets (
                    competition_slug, daily_submission_cap, submissions_today,
                    last_submission_date, timeout_seconds, memory_limit_mb
                ) VALUES (?, ?, 0, ?, ?, ?)
                ON CONFLICT(competition_slug) DO UPDATE SET
                    daily_submission_cap = excluded.daily_submission_cap,
                    timeout_seconds = excluded.timeout_seconds,
                    memory_limit_mb = excluded.memory_limit_mb;
                """,
                (competition_slug, cap, today, timeout_sec, mem_mb),
            )
            conn.commit()
        finally:
            conn.close()

    def get_budget(self, competition_slug: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM budgets WHERE competition_slug = ?", (competition_slug,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def increment_daily_submission(self, competition_slug: str) -> int:
        today = datetime.date.today().isoformat()
        conn = self._get_connection()
        try:
            budget = self.get_budget(competition_slug)
            if not budget:
                self.set_budget(competition_slug, cap=5, timeout_sec=300, mem_mb=4096)
                budget = self.get_budget(competition_slug)

            count = budget.get("submissions_today", 0)
            last_date = budget.get("last_submission_date")
            if last_date != today:
                count = 0

            count += 1
            conn.execute(
                """
                UPDATE budgets SET submissions_today = ?, last_submission_date = ?
                WHERE competition_slug = ?
                """,
                (count, today, competition_slug),
            )
            conn.commit()
            return count
        finally:
            conn.close()
