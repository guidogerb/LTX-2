from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vtx_app.config.env_layers import load_env
from vtx_app.config.settings import Settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  project_id TEXT PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  path TEXT NOT NULL,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS clips (
  project_id TEXT NOT NULL,
  clip_id TEXT NOT NULL,
  state TEXT NOT NULL,
  output_path TEXT,
  render_hash TEXT,
  updated_at TEXT,
  last_error TEXT,
  PRIMARY KEY(project_id, clip_id)
);
"""


@dataclass
class Registry:
    path: Path
    conn: sqlite3.Connection

    @staticmethod
    def load() -> "Registry":
        # Load env for settings
        load_env(project_env_path=None)
        s = Settings.from_env()
        s.app_home.mkdir(parents=True, exist_ok=True)
        db_path = s.app_home / "registry.sqlite"
        conn = sqlite3.connect(db_path)
        conn.executescript(SCHEMA)
        conn.commit()
        return Registry(path=db_path, conn=conn)

    def upsert_project(
        self, *, project_id: str, slug: str, title: str, path: str, updated_at: str
    ) -> None:
        self.conn.execute(
            "INSERT INTO projects(project_id, slug, title, path, updated_at) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(project_id) DO UPDATE SET "
            "slug=excluded.slug, title=excluded.title, path=excluded.path, updated_at=excluded.updated_at",
            (project_id, slug, title, path, updated_at),
        )
        self.conn.commit()

    def list_projects(self) -> list[dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT project_id, slug, title, path, updated_at FROM projects ORDER BY slug"
        )
        rows = cur.fetchall()
        return [
            {
                "project_id": r[0],
                "slug": r[1],
                "title": r[2],
                "path": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]

    def get_project_by_slug(self, slug: str) -> dict[str, Any] | None:
        cur = self.conn.execute(
            "SELECT project_id, slug, title, path, updated_at FROM projects WHERE slug = ?",
            (slug,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "project_id": row[0],
            "slug": row[1],
            "title": row[2],
            "path": row[3],
            "updated_at": row[4],
        }

    def upsert_clip(
        self,
        *,
        project_id: str,
        clip_id: str,
        state: str,
        output_path: str | None,
        render_hash: str | None,
        updated_at: str,
        last_error: str | None,
    ) -> None:
        self.conn.execute(
            "INSERT INTO clips(project_id, clip_id, state, output_path, render_hash, updated_at, last_error) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(project_id, clip_id) DO UPDATE SET state=excluded.state, output_path=excluded.output_path, "
            "render_hash=excluded.render_hash, updated_at=excluded.updated_at, last_error=excluded.last_error",
            (
                project_id,
                clip_id,
                state,
                output_path,
                render_hash,
                updated_at,
                last_error,
            ),
        )
        self.conn.commit()

    def list_unfinished_clips(self) -> list[dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT project_id, clip_id, state, output_path, updated_at FROM clips "
            "WHERE state IN ('planned','queued','rejected') ORDER BY updated_at"
        )
        rows = cur.fetchall()
        return [
            {
                "project_id": r[0],
                "clip_id": r[1],
                "state": r[2],
                "output_path": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]
