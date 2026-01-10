from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from vtx_app.cli import app

runner = CliRunner()


def test_projects_list():
    with patch("vtx_app.project.loader.Registry.load") as mock_load:
        mock_reg = MagicMock()
        mock_reg.list_projects.return_value = [
            {"slug": "p1", "title": "T1", "path": "/p1"}
        ]
        mock_load.return_value = mock_reg

        with patch("vtx_app.project.loader.ProjectLoader.sync_all_projects"):
            result = runner.invoke(app, ["projects", "list"])
            assert result.exit_code == 0
            assert "p1" in result.stdout
            assert "T1" in result.stdout


def test_projects_new(tmp_path):
    with patch("vtx_app.registry.db.Registry.load"):
        # Mock Registry.load() to return a mock
        pass

    # Actually mocking ProjectLoader inside cli
    with patch("vtx_app.cli.ProjectLoader") as MockLoader:
        mock_instance = MockLoader.return_value
        mock_instance.create_project.return_value = Path("/tmp/newp")

        result = runner.invoke(
            app, ["projects", "new", "myproj", "--title", "My Title"]
        )
        assert result.exit_code == 0
        assert "Created myproj" in result.stdout
        mock_instance.create_project.assert_called_with(slug="myproj", title="My Title")


def test_render_assemble():
    with patch("vtx_app.cli.Registry.load"), patch("vtx_app.cli.ProjectLoader"), patch(
        "vtx_app.render.assembler.Assembler"
    ) as MockAssembler:

        mock_asm = MockAssembler.return_value

        result = runner.invoke(
            app, ["render", "assemble", "proj1", "--output", "movie.mp4"]
        )
        assert result.exit_code == 0
        mock_asm.assemble.assert_called_with(output_name="movie.mp4")
