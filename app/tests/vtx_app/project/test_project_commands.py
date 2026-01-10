from __future__ import annotations

import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from vtx_app.cli import app
from vtx_app.project.loader import Project

runner = CliRunner()


@pytest.fixture
def mock_registry_load():
    with patch("vtx_app.cli.Registry.load") as mock:
        yield mock


@pytest.fixture
def mock_project_loader():
    with patch("vtx_app.cli.ProjectLoader") as mock:
        yield mock


def test_project_export(tmp_path, mock_registry_load, mock_project_loader):
    # Setup project structure
    proj_dir = tmp_path / "test_project"
    proj_dir.mkdir()
    (proj_dir / "project.env").write_text("ENV=1")
    (proj_dir / ".venv").mkdir()
    (proj_dir / ".venv" / "junk.txt").write_text("junk")

    # Mock loader returning project
    proj = Project(root=proj_dir)
    mock_registry_load.return_value = MagicMock()
    loader_instance = mock_project_loader.return_value
    loader_instance.load.return_value = proj

    # Execute command
    with runner.isolated_filesystem():
        result = runner.invoke(
            app, ["project", "export", "test_project", "--output", "my_export.zip"]
        )
        assert result.exit_code == 0
        assert "Exported" in result.stdout

        # Verify zip content
        assert Path("my_export.zip").exists()
        with zipfile.ZipFile("my_export.zip", "r") as z:
            files = z.namelist()
            assert "test_project/project.env" in files
            for f in files:
                assert ".venv" not in f
