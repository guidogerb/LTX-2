from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from vtx_app.config.env_layers import load_env
from vtx_app.config.settings import Settings


@dataclass
class Project:
    root: Path

    @property
    def metadata_path(self) -> Path:
        return self.root / "metadata.yaml"

    @property
    def project_env_path(self) -> Path:
        return self.root / "project.env"

    @property
    def venv_path(self) -> Path:
        return self.root / ".venv"

    def load_metadata(self) -> dict:
        return yaml.safe_load(self.metadata_path.read_text())

    def settings(self) -> Settings:
        load_env(project_env_path=self.project_env_path)
        return Settings.from_env()

    def create_venv(self) -> None:
        """
        Creates per-project venv using that project's env/requirements.txt.
        """
        req = self.root / "env" / "requirements.txt"
        if not req.exists():
            raise FileNotFoundError(req)

        # Create venv
        subprocess.check_call(["python", "-m", "venv", str(self.venv_path)])

        pip = self.venv_path / (
            "Scripts/pip.exe" if (self.venv_path / "Scripts").exists() else "bin/pip"
        )
        subprocess.check_call([str(pip), "install", "-r", str(req)])
