from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

import yaml
from rich import print

from vtx_app.config.env_layers import load_env
from vtx_app.config.settings import Settings
from vtx_app.registry.db import Registry
from vtx_app.project.layout import Project
from vtx_app.utils.timecode import now_iso


@dataclass
class ProjectLoader:
    registry: Registry

    def _app_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def _template_root(self) -> Path:
        return self._app_root() / "_global" / "templates" / "project_template"

    def sync_all_projects(self) -> None:
        load_env(project_env_path=None)
        s = Settings.from_env()
        s.projects_root.mkdir(parents=True, exist_ok=True)

        for p in sorted(s.projects_root.glob("*")):
            if not p.is_dir():
                continue
            meta = p / "metadata.yaml"
            if not meta.exists():
                continue
            try:
                data = yaml.safe_load(meta.read_text()) or {}
                self.registry.upsert_project(
                    project_id=str(data.get("project_id")),
                    slug=str(data.get("slug")),
                    title=str(data.get("title")),
                    path=str(p),
                    updated_at=str(data.get("updated_at", "")),
                )
            except Exception as e:
                print(f"[yellow]Skip[/yellow] {p}: {e}")

    def create_project(self, *, slug: str, title: str) -> Path:
        load_env(project_env_path=None)
        s = Settings.from_env()
        dest = s.projects_root / slug
        if dest.exists():
            raise FileExistsError(dest)

        shutil.copytree(self._template_root(), dest)

        meta_path = dest / "metadata.yaml"
        meta = yaml.safe_load(meta_path.read_text())
        meta["project_id"] = str(uuid.uuid4())
        meta["slug"] = slug
        meta["title"] = title
        meta["updated_at"] = now_iso()
        meta_path.write_text(yaml.safe_dump(meta, sort_keys=False))

        # Copy project.env.example -> project.env
        pe = dest / "project.env.example"
        if pe.exists():
            (dest / "project.env").write_text(pe.read_text())

        self.sync_all_projects()
        return dest

    def load(self, slug: str) -> Project:
        load_env(project_env_path=None)
        s = Settings.from_env()
        path = s.projects_root / slug
        if not path.exists():
            raise FileNotFoundError(path)
        return Project(root=path)
