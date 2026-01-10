from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from vtx_app.cli import app
from vtx_app.style_manager import StyleManager

runner = CliRunner()


@pytest.fixture
def mock_style_manager(tmp_path, monkeypatch):
    """Point style manager to a temp dir."""

    def mock_init(self):
        self.root = tmp_path / "global_styles"
        self.root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(StyleManager, "__init__", mock_init)


def test_create_style(tmp_path, mock_style_manager):
    """Test extracting a style from a project."""
    # Setup dummy project
    proj_root = tmp_path / "projects" / "p1"
    proj_root.mkdir(parents=True)
    (proj_root / "prompts").mkdir()

    # Write artifacts
    (proj_root / "prompts" / "style_bible.yaml").write_text(
        yaml.safe_dump({"StyleBible": {"Format": {"AspectRatio": "16:9"}}})
    )
    (proj_root / "prompts" / "loras.yaml").write_text(
        yaml.safe_dump({"bundles": {"civitai_candidates": [{"name": "L1"}]}})
    )

    # Mock ProjectLoader to return this path
    with patch("vtx_app.cli.Registry.load"), patch(
        "vtx_app.cli.ProjectLoader"
    ) as MockLoader:

        mock_proj = MagicMock()
        mock_proj.root = proj_root
        MockLoader.return_value.load.return_value = mock_proj

        # We also need to mock _get_slug to return 'p1' if passed
        # But _get_slug is imported in cli, so patch cli._get_slug?
        # Actually it's defined in cli.py, so vtx_app.cli._get_slug
        with patch("vtx_app.cli._get_slug", return_value="p1"):
            result = runner.invoke(app, ["create-style", "my_style", "p1"])

            assert result.exit_code == 0
            assert "Style 'my_style' saved" in result.stdout

            # Verify file created in mock style/global root
            mgr = StyleManager()
            style_data = mgr.load_style("my_style")
            assert style_data is not None
            assert style_data["meta"]["source_project"] == "p1"
            assert style_data["style_bible"]["Format"]["AspectRatio"] == "16:9"
            assert len(style_data["resources"]["bundles"]) == 1


def test_create_movie_automation(tmp_path, mock_style_manager):
    """Test the end-to-end create-movie command (mocked)."""

    # vtx_app.cli.ProposalGenerator is invalid because it's imported INSIDE the function.
    # We must patch where it is defined, OR patch 'sys.modules' trickery,
    # OR simpler: because it is imported inside the function, we have to patch it in the module
    # where the CLASS is defined, IF the function imports it from there.
    # In cli.py: from vtx_app.wizards.proposal import ProposalGenerator
    # So we patch vtx_app.wizards.proposal.ProposalGenerator.

    with patch("vtx_app.cli.Settings") as MockSettings, patch(
        "vtx_app.wizards.proposal.ProposalGenerator"
    ) as MockPropGen, patch("vtx_app.registry.db.Registry.load"), patch(
        "vtx_app.project.loader.ProjectLoader"
    ) as MockLoader, patch(
        "vtx_app.story.openai_builder.StoryBuilder"
    ) as MockBuilder:

        # 1. Settings
        mock_sets = MagicMock()
        MockSettings.from_env.return_value = mock_sets

        # 2. Proposal
        mock_gen = MockPropGen.return_value
        mock_gen.create_proposal.return_value = {
            "meta": {"slug": "auto_movie", "title": "Auto Title"},
            "story": {"brief": "Brief"},
            "resources": {"suggested_loras": []},
        }

        # 3. Loader
        mock_loader_inst = MockLoader.return_value
        proj_path = tmp_path / "projects" / "auto_movie"
        proj_path.mkdir(parents=True)
        (proj_path / "story").mkdir()
        (proj_path / "prompts").mkdir()

        mock_loader_inst.create_project.return_value = proj_path

        mock_proj = MagicMock()
        mock_proj.root = proj_path
        mock_loader_inst.load.return_value = mock_proj

        # 4. Builder
        mock_builder_inst = MockBuilder.return_value

        # Run command in tmp_path so plan write works
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["create-movie", "auto_movie", "A prompt"])

            assert result.exit_code == 0

            # Assert flow
            mock_gen.create_proposal.assert_called_once_with("A prompt")
            mock_loader_inst.create_project.assert_called_once()

            # Assert Builder steps
            mock_builder_inst.generate_style_bible.assert_called_once()
            mock_builder_inst.generate_outline.assert_called_once()
            mock_builder_inst.generate_treatment.assert_called_once()
            mock_builder_inst.generate_shotlist.assert_called_once()
            mock_builder_inst.generate_clip_specs.assert_called_once()

            # Verify plan was moved
            assert (proj_path / "auto_movie_plan.yaml").exists()


def test_list_styles(tmp_path, mock_style_manager):
    """Test the list-styles command."""

    # 1. Start empty
    result = runner.invoke(app, ["list-styles"])
    assert result.exit_code == 0
    assert "No styles found" in result.stdout

    # 2. Add a style manually
    mgr = StyleManager()
    (mgr.root / "style_a.yaml").write_text("meta:\n  name: style_a")
    (mgr.root / "style_b.yaml").write_text("meta:\n  name: style_b")

    # 3. List again
    result = runner.invoke(app, ["list-styles"])
    assert result.exit_code == 0
    assert "style_a" in result.stdout
    assert "style_b" in result.stdout
    assert "Available Styles (2):" in result.stdout


def test_create_style_with_description(tmp_path, mock_style_manager):
    """Test creating a style with a description."""
    proj_root = tmp_path / "projects" / "p_desc"
    proj_root.mkdir(parents=True)
    (proj_root / "prompts").mkdir()

    (proj_root / "prompts" / "style_bible.yaml").write_text(
        yaml.safe_dump({"StyleBible": {}})
    )

    with patch("vtx_app.cli.Registry.load"), patch(
        "vtx_app.cli.ProjectLoader"
    ) as MockLoader:
        mock_proj = MagicMock()
        mock_proj.root = proj_root
        MockLoader.return_value.load.return_value = mock_proj

        with patch("vtx_app.cli._get_slug", return_value="p_desc"):
            result = runner.invoke(
                app, ["create-style", "desc_style", "p_desc", "A cool style"]
            )

            assert result.exit_code == 0
            assert "Style 'desc_style' saved" in result.stdout

            mgr = StyleManager()
            style_data = mgr.load_style("desc_style")
            assert style_data["meta"]["description"] == "A cool style"

            # Test listing shows description
            res_list = runner.invoke(app, ["list-styles"])
            assert "A cool style" in res_list.stdout


def test_delete_style(tmp_path, mock_style_manager):
    """Test deleting a style."""
    mgr = StyleManager()
    style_path = mgr.root / "to_delete.yaml"
    style_path.write_text(yaml.safe_dump({"meta": {"name": "to_delete"}}))

    assert style_path.exists()

    result = runner.invoke(app, ["delete-style", "to_delete"])
    assert result.exit_code == 0
    assert "deleted" in result.stdout
    assert not style_path.exists()

    # Test delete non-existent
    result = runner.invoke(app, ["delete-style", "non_existent"])
    assert result.exit_code == 0
    assert "not found" in result.stdout


def test_update_style_desc(tmp_path, mock_style_manager):
    """Test updating style description."""
    mgr = StyleManager()
    style_path = mgr.root / "to_update.yaml"
    style_path.write_text(
        yaml.safe_dump({"meta": {"name": "to_update", "description": "old"}})
    )

    assert style_path.exists()

    result = runner.invoke(app, ["update-style-desc", "to_update", "new description"])
    assert result.exit_code == 0
    assert "updated" in result.stdout

    data = yaml.safe_load(style_path.read_text())
    assert data["meta"]["description"] == "new description"

    # Test update non-existent
    result = runner.invoke(app, ["update-style-desc", "non_existent", "desc"])
    assert result.exit_code == 0
    assert "not found" in result.stdout
