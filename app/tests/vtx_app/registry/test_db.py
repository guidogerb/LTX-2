import sqlite3

import pytest

from vtx_app.registry.db import SCHEMA, Registry


@pytest.fixture
def registry(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return Registry(path=db_path, conn=conn)


def test_upsert_project(registry):
    registry.upsert_project(
        project_id="p1",
        slug="proj1",
        title="T1",
        path="/tmp/p1",
        updated_at="2024-01-01",
    )
    projs = registry.list_projects()
    assert len(projs) == 1
    assert projs[0]["slug"] == "proj1"

    # Update
    registry.upsert_project(
        project_id="p1",
        slug="proj1_new",
        title="T2",
        path="/tmp/p1",
        updated_at="2024-01-02",
    )
    projs = registry.list_projects()
    assert len(projs) == 1
    assert projs[0]["slug"] == "proj1_new"
    assert projs[0]["title"] == "T2"


def test_upsert_clip(registry):
    registry.upsert_clip(
        project_id="p1",
        clip_id="c1",
        state="planned",
        output_path=None,
        render_hash=None,
        updated_at="2024",
        last_error=None,
    )

    # We don't have get_clip method, but we can verify via list_unfinished_clips if simple enough
    # or just raw SQL
    cur = registry.conn.execute("SELECT * FROM clips WHERE clip_id='c1'")
    row = cur.fetchone()
    assert row is not None
    assert row[2] == "planned"  # state

    # Update
    registry.upsert_clip(
        project_id="p1",
        clip_id="c1",
        state="rendered",
        output_path="out.mp4",
        render_hash="hash",
        updated_at="2025",
        last_error=None,
    )
    cur = registry.conn.execute("SELECT output_path FROM clips WHERE clip_id='c1'")
    assert cur.fetchone()[0] == "out.mp4"


def test_list_unfinished(registry):
    registry.upsert_clip(
        project_id="p1",
        clip_id="c1",
        state="planned",
        output_path="",
        render_hash="",
        updated_at="",
        last_error=None,
    )
    registry.upsert_clip(
        project_id="p1",
        clip_id="c2",
        state="rendered",
        output_path="",
        render_hash="",
        updated_at="",
        last_error=None,
    )

    unfinished = registry.list_unfinished_clips()
    assert len(unfinished) == 1
    assert unfinished[0]["clip_id"] == "c1"
