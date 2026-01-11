from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from vtx_app.cli import app

runner = CliRunner()


@dataclass
class MockSettingsData:
    projects_root: Path = Path("/tmp/projects")
    models_root: Path = Path("/tmp/models")


@pytest.fixture
def mock_deps():
    # We need to patch sources for local imports, AND global references in cli.py

    with patch("vtx_app.registry.db.Registry") as MockRegistrySource, patch(
        "vtx_app.project.loader.ProjectLoader"
    ) as MockLoaderSource, patch(
        "vtx_app.story.openai_builder.StoryBuilder"
    ) as MockBuilderSource, patch(
        "vtx_app.render.renderer.RenderController"
    ) as MockRendererSource, patch(
        "vtx_app.config.settings.Settings"
    ) as MockSettingsSource, patch(
        "vtx_app.config.env_layers.load_env"
    ) as MockLoadEnvSource, patch(
        "vtx_app.render.assembler.Assembler"
    ) as MockAssembler, patch(
        "vtx_app.style_manager.StyleManager"
    ) as MockStyleMgr, patch(
        "vtx_app.wizards.proposal.ProposalGenerator"
    ) as MockProposalGen, patch(
        "vtx_app.producer.Director"
    ) as MockDirector:

        # Apply these mocks to vtx_app.cli globals as well
        with patch("vtx_app.cli.Registry", MockRegistrySource), patch(
            "vtx_app.cli.ProjectLoader", MockLoaderSource
        ), patch("vtx_app.cli.StoryBuilder", MockBuilderSource), patch(
            "vtx_app.cli.RenderController", MockRendererSource
        ), patch(
            "vtx_app.cli.Settings", MockSettingsSource
        ), patch(
            "vtx_app.cli.load_env", MockLoadEnvSource
        ), patch(
            "vtx_app.cli.StyleManager", MockStyleMgr
        ), patch(
            "vtx_app.cli.Assembler", MockAssembler
        ), patch(
            "vtx_app.cli.Director", MockDirector
        ), patch(
            "vtx_app.cli.ProposalGenerator", MockProposalGen
        ):

            reg = MockRegistrySource.load.return_value
            loader = MockLoaderSource.return_value

            # Setup common mock behavior
            proj = MagicMock()
            proj.root = Path("/tmp/proj")
            proj.project_env_path = Path("/tmp/proj/project.env")
            loader.load.return_value = proj
            loader.create_project.return_value = Path("/tmp/proj")

            # Setup Settings to behave like dataclass for asdict()
            settings_obj = MockSettingsData()
            MockSettingsSource.from_env.return_value = settings_obj

            yield {
                "reg": reg,
                "loader": loader,
                "project": proj,
                "builder": MockBuilderSource.return_value,
                "renderer": MockRendererSource.return_value,
                "assembler": MockAssembler.return_value,
                "style_mgr": MockStyleMgr.return_value,
                "proposal_gen": MockProposalGen.return_value,
                "director": MockDirector.return_value,
                "settings": settings_obj,
                "load_env": MockLoadEnvSource,
                "MockStyleMgr": MockStyleMgr,
                "MockBuilderClass": MockBuilderSource,
                "MockRendererClass": MockRendererSource,
                "MockAssemblerClass": MockAssembler,
                "MockProposalGenClass": MockProposalGen,
            }


# --- Root Commands ---


def test_clean(mock_deps):
    with runner.isolated_filesystem():
        (Path.cwd() / "__pycache__").mkdir()
        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "Removed 1 __pycache__" in result.stdout


def test_list_styles(mock_deps):
    mock_deps["style_mgr"].list_styles.return_value = ["s1"]
    mock_deps["style_mgr"].load_style.return_value = {"meta": {"description": "desc"}}

    result = runner.invoke(app, ["list-styles"])
    assert result.exit_code == 0
    assert "s1" in result.stdout
    assert "desc" in result.stdout

    mock_deps["style_mgr"].list_styles.return_value = []
    result = runner.invoke(app, ["list-styles"])
    assert "No styles found" in result.stdout


def test_review(mock_deps):
    proj = mock_deps["project"]
    proj.root = MagicMock()

    with patch("subprocess.run"):
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = [True]

            result = runner.invoke(app, ["review", "test-slug"])
            assert result.exit_code == 0
            assert "Opening" in result.stdout


def test_review_not_found(mock_deps):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False
        result = runner.invoke(app, ["review", "test-slug"])
        assert result.exit_code == 0
        assert "No video found" in result.stdout


def test_produce(mock_deps):
    result = runner.invoke(app, ["produce", "slug", "-c", "concept"])
    assert result.exit_code == 0
    mock_deps["director"].produce.assert_called_with(
        slug="slug", concept="concept", title=None, auto_render=False
    )


def test_produce_auto_render(mock_deps):
    result = runner.invoke(app, ["produce", "slug", "-c", "concept", "--render"])
    assert result.exit_code == 0
    mock_deps["director"].produce.assert_called_with(
        slug="slug", concept="concept", title=None, auto_render=True
    )


def test_create_style(mock_deps):
    mock_deps["style_mgr"].save_style.return_value = Path("/tmp/style.yaml")
    result = runner.invoke(app, ["create-style", "new_style", "slug", "desc"])

    assert result.exit_code == 0
    mock_deps["style_mgr"].save_style.assert_called()
    assert "saved to" in result.stdout


def test_delete_style(mock_deps):
    mock_deps["style_mgr"].delete_style.return_value = True
    result = runner.invoke(app, ["delete-style", "s1"])
    assert result.exit_code == 0
    assert "deleted" in result.stdout


def test_update_style_desc(mock_deps):
    mock_deps["style_mgr"].update_description.return_value = True
    result = runner.invoke(app, ["update-style-desc", "s1", "new"])
    assert result.exit_code == 0
    assert "updated" in result.stdout


def test_render_reviews(mock_deps):
    proj = mock_deps["project"]
    proj.root = Path("/tmp/root")

    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.glob"
    ) as mock_glob:
        mock_exists.return_value = True
        p1 = MagicMock()
        p1.name = "c1.yaml"
        p1.stem = "c1"
        mock_glob.return_value = [p1]

        result = runner.invoke(app, ["render-reviews", "slug"])
        assert result.exit_code == 0
        mock_deps["renderer"].render_clip.assert_called_with(
            clip_id="c1",
            resolution_scale=0.5,
            output_dir=proj.root / "renders" / "low-res",
        )


def test_render_review(mock_deps):
    result = runner.invoke(app, ["render-review", "slug", "c1"])
    assert result.exit_code == 0
    mock_deps["renderer"].render_clip.assert_called()


def test_render_full(mock_deps):
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.glob"
    ) as mock_glob:
        mock_exists.return_value = True
        p1 = MagicMock()
        p1.name = "c1.yaml"
        p1.stem = "c1"
        mock_glob.return_value = [p1]

        result = runner.invoke(app, ["render-full", "slug"])
        assert result.exit_code == 0
        mock_deps["renderer"].render_clip.assert_called_with(
            clip_id="c1", preset="final", resolution_scale=1.0, output_dir=ANY
        )


def test_assemble(mock_deps):
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True
        result = runner.invoke(app, ["assemble", "slug"])
        assert result.exit_code == 0
        mock_deps["assembler"].assemble.assert_called()


def test_create_movie(mock_deps):
    mock_deps["proposal_gen"].create_proposal.return_value = {
        "meta": {"slug": "slug", "title": "Title"},
        "story": {"brief": "Brief"},
        "resources": {
            "suggested_loras": [{"name": "L1", "url": "u1", "download_url": "d1"}]
        },
    }

    with runner.isolated_filesystem():
        cwd = Path.cwd()
        mock_deps["loader"].create_project.return_value = cwd / "slug"
        (cwd / "slug" / "prompts").mkdir(parents=True)
        (cwd / "slug" / "story").mkdir(parents=True)
        proj = MagicMock()
        proj.root = cwd / "slug"
        mock_deps["loader"].load.return_value = proj

        result = runner.invoke(app, ["create-movie", "slug", "prompt"])
        assert result.exit_code == 0, result.stdout
        assert (cwd / "slug" / "slug_plan.yaml").exists()
        assert (cwd / "slug" / "story" / "00_brief.md").read_text() == "Brief"

        mock_deps["builder"].generate_outline.assert_called()


def test_create_movie_exists(mock_deps):
    mock_deps["proposal_gen"].create_proposal.return_value = {
        "meta": {"slug": "slug", "title": "Title"},
        "story": {"brief": "Brief"},
    }
    mock_deps["loader"].create_project.side_effect = FileExistsError("Exists")

    with runner.isolated_filesystem():
        with patch("shutil.move") as mock_move:
            cwd = Path.cwd()
            (cwd / "slug" / "story").mkdir(parents=True)

            proj = mock_deps["project"]
            proj.root = cwd / "slug"
            mock_deps["loader"].load.return_value = proj

            result = runner.invoke(app, ["create-movie", "slug", "prompt"])
            assert result.exit_code == 0
            assert "already exists" in result.stdout
            mock_move.assert_called()


def test_create_movie_merge_loras(mock_deps):
    mock_deps["proposal_gen"].create_proposal.return_value = {
        "meta": {"slug": "slug"},
        "story": {},
        "resources": {
            "suggested_loras": [{"name": "L2", "url": "u", "download_url": "d"}]
        },
    }

    with runner.isolated_filesystem():
        cwd = Path.cwd()
        mock_deps["loader"].create_project.return_value = cwd / "slug"
        (cwd / "slug" / "prompts").mkdir(parents=True)
        (cwd / "slug" / "story").mkdir(parents=True)
        (cwd / "slug" / "prompts" / "loras.yaml").write_text("bundles: {}")

        proj = mock_deps["project"]
        proj.root = cwd / "slug"
        mock_deps["loader"].load.return_value = proj

        result = runner.invoke(app, ["create-movie", "slug", "prompt"])
        assert result.exit_code == 0
        content = (cwd / "slug" / "prompts" / "loras.yaml").read_text()
        assert "L2" in content


def test_create_movie_all(mock_deps):
    mock_deps["proposal_gen"].create_proposal.return_value = {
        "meta": {"slug": "slug", "title": "Title"},
        "story": {"brief": "Brief"},
    }
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        mock_deps["loader"].create_project.return_value = cwd / "slug"
        (cwd / "slug" / "prompts").mkdir(parents=True)
        (cwd / "slug" / "story").mkdir(parents=True)
        proj = MagicMock()
        proj.root = cwd / "slug"
        mock_deps["loader"].load.return_value = proj

        with patch.object(Path, "glob", return_value=[Path("c1.yaml")]), patch.object(
            Path, "exists", return_value=True
        ):

            result = runner.invoke(app, ["create-movie-all", "slug", "prompt"])
            assert result.exit_code == 0
            mock_deps["renderer"].render_clip.assert_called()
            mock_deps["assembler"].assemble.assert_called()


# --- Projects App ---


def test_projects_list(mock_deps):
    mock_deps["reg"].list_projects.return_value = [
        {"slug": "p1", "title": "t1", "path": "path"}
    ]
    result = runner.invoke(app, ["projects", "list"])
    assert result.exit_code == 0
    assert "p1" in result.stdout


def test_projects_new(mock_deps):
    result = runner.invoke(app, ["projects", "new", "test", "--title", "Test"])
    assert result.exit_code == 0
    mock_deps["loader"].create_project.assert_called_with(slug="test", title="Test")


def test_projects_propose(mock_deps):
    mock_deps["proposal_gen"].create_proposal.return_value = {"meta": {"slug": "s"}}
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["projects", "propose", "concept"])
        assert result.exit_code == 0
        assert Path("s_plan.yaml").exists()


def test_projects_create_from_plan(mock_deps):
    with runner.isolated_filesystem():
        p = Path("plan.yaml")
        p.write_text(
            yaml.dump({"meta": {"slug": "s", "title": "t"}, "story": {"brief": "b"}})
        )

        cwd = Path.cwd()
        mock_deps["loader"].create_project.return_value = cwd / "s"
        proj_root = cwd / "s"
        (proj_root / "story").mkdir(parents=True)
        proj = MagicMock()
        proj.root = proj_root
        mock_deps["loader"].load.return_value = proj

        result = runner.invoke(app, ["projects", "create-from-plan", "plan.yaml"])
        assert result.exit_code == 0
        assert (proj_root / "story" / "00_brief.md").read_text() == "b"


# --- Project App ---


def test_project_env_create(mock_deps):
    result = runner.invoke(app, ["project", "env-create", "slug"])
    assert result.exit_code == 0
    mock_deps["project"].create_venv.assert_called()


def test_project_export(mock_deps):
    with runner.isolated_filesystem():
        proj_dir = Path("myproj")
        proj_dir.mkdir()
        mock_deps["project"].root = proj_dir.resolve()

        result = runner.invoke(
            app, ["project", "export", "slug", "--output", "out.zip"]
        )
        assert result.exit_code == 0
        assert Path("out.zip").exists()


# --- Story App ---


def test_story_commands(mock_deps):
    calls = [
        ("outline", "generate_outline"),
        ("treatment", "generate_treatment"),
        ("screenplay", "generate_screenplay"),
        ("characters", "generate_characters"),
        ("locations", "generate_locations"),
        ("shotlist", "generate_shotlist"),
    ]

    for cmd, method in calls:
        result = runner.invoke(app, ["story", cmd, "slug"])
        assert result.exit_code == 0
        getattr(mock_deps["builder"], method).assert_called()


def test_story_clips(mock_deps):
    result = runner.invoke(app, ["story", "clips", "slug", "--overwrite"])
    assert result.exit_code == 0
    mock_deps["builder"].generate_clip_specs.assert_called_with(
        overwrite=True, act=None, scene=None
    )


# --- Render App ---


def test_render_status(mock_deps):
    proj = mock_deps["project"]
    proj.root = Path("/tmp/proj")

    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.glob"
    ) as mock_glob, patch("pathlib.Path.read_text"):

        mock_exists.return_value = True
        p = MagicMock()
        p.stem = "clip1"
        p.read_text.return_value = "outputs: {mp4: 'renders/c1.mp4'}"
        mock_glob.return_value = [p]

        result = runner.invoke(app, ["render", "status", "slug"])
        assert result.exit_code == 0
        assert "clip1" in result.stdout


def test_render_clip(mock_deps):
    result = runner.invoke(app, ["render", "clip", "slug", "c1", "--preset", "high"])
    assert result.exit_code == 0
    mock_deps["renderer"].render_clip.assert_called_with(clip_id="c1", preset="high")


def test_render_approve(mock_deps):
    proj = mock_deps["project"]
    proj.root = Path("/tmp/proj")

    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.read_text"
    ) as mock_read, patch("pathlib.Path.write_text") as mock_write:

        mock_exists.return_value = True
        mock_read.return_value = "render: {approved: false}"

        result = runner.invoke(app, ["render", "approve", "slug", "c1"])
        assert result.exit_code == 0

        # Verify updated content written
        args = mock_write.call_args[0][0]
        data = yaml.safe_load(args)
        assert data["render"]["approved"] is True


def test_render_resume(mock_deps):
    result = runner.invoke(app, ["render", "resume"])
    assert result.exit_code == 0
    mock_deps["renderer"].resume.assert_called()


def test_render_assemble_cmd(mock_deps):
    result = runner.invoke(app, ["render", "assemble", "slug"])
    assert result.exit_code == 0
    mock_deps["assembler"].assemble.assert_called()


# --- Config App ---


def test_config_show(mock_deps):
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0


def test_config_show_with_project(mock_deps):
    # Test 'config show -p slug'
    runner.invoke(app, ["config", "show", "-p", "slug"])
    mock_deps["load_env"].assert_called()


def test_review_platforms(mock_deps):
    proj = mock_deps["project"]
    proj.root = MagicMock()
    with patch("pathlib.Path.exists", return_value=True):
        # Darwin
        with patch("sys.platform", "darwin"), patch("subprocess.run") as m_run:
            runner.invoke(app, ["review", "s"])
            m_run.assert_called_with(["open", ANY])

        # Win32
        with patch("sys.platform", "win32"), patch(
            "os.startfile", create=True
        ) as m_start:
            runner.invoke(app, ["review", "s"])
            m_start.assert_called()

        # Linux no xdg
        with patch("sys.platform", "linux"), patch("shutil.which", return_value=None):
            res = runner.invoke(app, ["review", "s"])
            assert "File:" in res.stdout


def test_render_reviews_no_clips(mock_deps):
    proj = mock_deps["project"]
    proj.root = Path("/tmp/proj")

    # CASE 1: clips dir doesn't exist
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False
        res = runner.invoke(app, ["render-reviews", "s"])
        assert "No clips found" in res.stdout

    # CASE 2: clips dir exists but empty
    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.glob", return_value=[]
    ):
        res = runner.invoke(app, ["render-reviews", "s"])
        assert "No clips found" in res.stdout


def test_render_reviews_exception(mock_deps):
    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.glob", return_value=[Path("c1.yaml")]
    ):

        mock_deps["renderer"].render_clip.side_effect = Exception("Boom")
        res = runner.invoke(app, ["render-reviews", "s"])
        assert "Failed to render" in res.stdout


def test_render_full_exception(mock_deps):
    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.glob", return_value=[Path("c1.yaml")]
    ):
        mock_deps["renderer"].render_clip.side_effect = Exception("Fail")
        res = runner.invoke(app, ["render-full", "s"])
        assert "Failed to render" in res.stdout


def test_render_approve_warning(mock_deps):
    proj = mock_deps["project"]
    proj.root = Path("/tmp/proj")

    def side_effect(self):
        # The mock gets 'self' because autospec is True, or it matches call signature?
        # If I patch Path.exists, self is the path object.
        if "out.mp4" in str(self):
            return False
        return True

    with patch("pathlib.Path.exists", autospec=True, side_effect=side_effect), patch(
        "pathlib.Path.read_text",
        return_value="render: {strategy: v2v}\noutputs: {mp4: out.mp4}",
    ), patch("pathlib.Path.write_text"):

        res = runner.invoke(app, ["render", "approve", "s", "c1", "--strategy", "v2v"])
        assert "Warning" in res.stdout


def test_render_approve_not_found(mock_deps):
    with patch("pathlib.Path.exists", return_value=False):
        res = runner.invoke(app, ["render", "approve", "s", "c1"])
        assert "not found" in res.stdout


def test_story_outline_infer_slug(mock_deps):
    """Test _get_slug inference failure/success logic"""
    # Success case: inside project root
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = Path("/tmp/projects/p1")
        mock_deps["settings"].projects_root = Path("/tmp/projects")

        # We need to mock relative_to behavior since paths are mocked
        # But wait, Path objects are real objects in my test, just cwd returns one.

        result = runner.invoke(app, ["story", "outline"])
        assert result.exit_code == 0
        mock_deps["builder"].generate_outline.assert_called()


def test_story_outline_infer_slug_fail(mock_deps):
    # Fail case: outside
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = Path("/tmp/other")
        mock_deps["settings"].projects_root = Path("/tmp/projects")

        result = runner.invoke(app, ["story", "outline"])
        assert result.exit_code == 1
        assert "Not in a project directory" in result.stdout


def test_story_outline_infer_slug_root(mock_deps):
    # Fail case: at root
    with patch("pathlib.Path.cwd") as mock_cwd:
        mock_cwd.return_value = Path("/tmp/projects")
        mock_deps["settings"].projects_root = Path("/tmp/projects")

        result = runner.invoke(app, ["story", "outline"])
        assert result.exit_code == 1
        assert "Cannot infer" in result.stdout
