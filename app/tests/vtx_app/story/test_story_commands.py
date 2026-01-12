from __future__ import annotations

from unittest.mock import patch

import pytest
import yaml
from vtx_app.project.loader import Project
from vtx_app.story.openai_builder import StoryBuilder


@pytest.fixture
def mock_project(tmp_path):
    """Creates a temporary project structure."""
    proj_dir = tmp_path / "test_project"
    proj_dir.mkdir()
    (proj_dir / "story").mkdir()
    (proj_dir / "prompts").mkdir()
    (proj_dir / "story" / "00_brief.md").write_text("A test brief.")
    (proj_dir / "story" / "01_outline.yaml").write_text("outline: []")

    return Project(root=proj_dir)


def test_generate_screenplay(mock_project):
    with patch("vtx_app.story.openai_builder.StoryBuilder._call_structured") as mock_call:
        mock_call.return_value = {"screenplay": [{"slug": "INT. ROOM", "text": "Hello"}]}

        builder = StoryBuilder(project=mock_project)
        builder.generate_screenplay()

        out_file = mock_project.root / "story" / "03_screenplay.yaml"
        assert out_file.exists()
        data = yaml.safe_load(out_file.read_text())
        assert data["screenplay"][0]["slug"] == "INT. ROOM"

        mock_call.assert_called_once()


def test_generate_characters(mock_project):
    with patch("vtx_app.story.openai_builder.StoryBuilder._call_structured") as mock_call:
        # Strict schema returns list of objects
        mock_call.return_value = {"characters": [{"name": "Alice", "description": "A girl"}]}

        builder = StoryBuilder(project=mock_project)
        builder.generate_characters()

        out_file = mock_project.root / "prompts" / "characters.yaml"
        assert out_file.exists()
        data = yaml.safe_load(out_file.read_text())
        # Implementation transforms back to dict for generic usage
        assert data["characters"]["Alice"]["description"] == "A girl"

        mock_call.assert_called_once()


def test_generate_locations(mock_project):
    with patch("vtx_app.story.openai_builder.StoryBuilder._call_structured") as mock_call:
        # Strict schema returns list of objects
        mock_call.return_value = {"locations": [{"name": "Park", "description": "Green trees"}]}

        builder = StoryBuilder(project=mock_project)
        builder.generate_locations()

        out_file = mock_project.root / "prompts" / "locations.yaml"
        assert out_file.exists()
        data = yaml.safe_load(out_file.read_text())
        assert data["locations"]["Park"]["description"] == "Green trees"

        mock_call.assert_called_once()


def test_generate_treatment(mock_project):
    with patch("vtx_app.story.openai_builder.StoryBuilder._call_structured") as mock_call:
        mock_call.return_value = {
            "title": "My Movie",
            "content": "The story begins...",
        }

        builder = StoryBuilder(project=mock_project)
        builder.generate_treatment()

        out_file = mock_project.root / "story" / "02_treatment.md"
        assert out_file.exists()
        content = out_file.read_text()
        assert "# My Movie" in content
        assert "The story begins..." in content

        mock_call.assert_called_once()
