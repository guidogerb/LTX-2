from __future__ import annotations

from unittest.mock import patch

import pytest
import yaml
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


def test_render_status(tmp_path, mock_registry_load, mock_project_loader):
    # Setup project structure
    proj_dir = tmp_path / "test_project"
    proj_dir.mkdir()
    clips_dir = proj_dir / "prompts" / "clips"
    clips_dir.mkdir(parents=True)

    # Clip 1: Done
    (clips_dir / "clip_01.yaml").write_text(
        yaml.safe_dump({"outputs": {"mp4": "render/clip_01.mp4"}})
    )
    (proj_dir / "render").mkdir()
    (proj_dir / "render" / "clip_01.mp4").write_text("video content")

    # Clip 2: Pending
    (clips_dir / "clip_02.yaml").write_text(
        yaml.safe_dump({"outputs": {"mp4": "render/clip_02.mp4"}})
    )

    # Clip 3: Broken
    (clips_dir / "clip_03.yaml").write_text("invalid yaml: {")

    # Mock loader
    proj = Project(root=proj_dir)
    loader_instance = mock_project_loader.return_value
    loader_instance.load.return_value = proj

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["render", "status", "test_project"])
        assert result.exit_code == 0
        assert "Render Status: test_project" in result.stdout
        assert "clip_01" in result.stdout
        assert "Done" in result.stdout
        assert "clip_02" in result.stdout
        assert "Pending" in result.stdout
        assert "clip_03" in result.stdout
        # Rich table formatting might separate columns, but the text should be there.
