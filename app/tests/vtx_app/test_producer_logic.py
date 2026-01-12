from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from vtx_app.producer import Director
from vtx_app.project.loader import Project


@pytest.fixture
def mock_project(tmp_path):
    proj_dir = tmp_path / "test_project"
    proj_dir.mkdir()
    (proj_dir / "story").mkdir()
    (proj_dir / "prompts").mkdir()
    (proj_dir / "env").mkdir()
    (proj_dir / "prompts" / "clips").mkdir(parents=True)
    return Project(root=proj_dir)


def test_director_produce_flow(mock_project):
    # Mock Loader
    loader = MagicMock()
    loader.load.return_value = mock_project
    # Mock Registry
    reg = MagicMock()

    director = Director(registry=reg, loader=loader)

    # Create a dummy clip to ensure render script includes render commands
    (mock_project.root / "prompts" / "clips" / "clip_01.yaml").touch()

    # Patch StoryBuilder to avoid OpenAI calls
    with patch("vtx_app.producer.StoryBuilder") as MockBuilder:
        builder_instance = MockBuilder.return_value

        # Run produce
        director.produce(
            slug="test_project",
            concept="A brief concept.",
            title="Test Project",
            auto_render=False,
        )

        # assertions
        assert (mock_project.root / "story" / "00_brief.md").read_text() == "A brief concept."

        # Verify sequence
        builder_instance.generate_outline.assert_called_once()
        builder_instance.generate_treatment.assert_called_once()
        builder_instance.generate_screenplay.assert_called_once()
        builder_instance.generate_characters.assert_called_once()
        builder_instance.generate_locations.assert_called_once()
        builder_instance.generate_shotlist.assert_called_once()
        builder_instance.generate_clip_specs.assert_called_once()

        # Verify render script generation
        script = mock_project.root / "render_all.sh"
        assert script.exists()
        assert "vtx render assemble" in script.read_text()
