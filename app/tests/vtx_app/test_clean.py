from pathlib import Path

from typer.testing import CliRunner
from vtx_app.cli import app

runner = CliRunner()


def test_clean():
    with runner.isolated_filesystem() as td:
        root = Path(td)
        # Create some pycache dirs
        (root / "src" / "__pycache__").mkdir(parents=True)
        (root / "tests" / "__pycache__").mkdir(parents=True)
        (root / "other").mkdir()

        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "Removed 2 __pycache__" in result.stdout

        assert not (root / "src" / "__pycache__").exists()
        assert not (root / "tests" / "__pycache__").exists()
        assert (root / "other").exists()
