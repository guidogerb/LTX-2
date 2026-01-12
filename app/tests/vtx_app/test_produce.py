from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner
from vtx_app.cli import app

runner = CliRunner()


@pytest.fixture
def mock_registry_load():
    with patch("vtx_app.cli.Registry.load") as mock:
        yield mock


@pytest.fixture
def mock_project_loader():
    with patch("vtx_app.cli.ProjectLoader") as mock:
        yield mock


@pytest.fixture
def mock_director():
    with patch("vtx_app.producer.Director") as mock:
        yield mock


def test_produce_command(tmp_path, mock_registry_load, mock_project_loader):
    # Mock return values
    reg = MagicMock()
    mock_registry_load.return_value = reg
    loader = MagicMock()
    mock_project_loader.return_value = loader

    # Logic is implemented inside produce(), so we mock the Director class *where it is imported*
    # vtx_app.cli.produce imports Director inside the function from vtx_app.producer
    # So we patch 'vtx_app.producer.Director' (if imported locally, patch where defined or sys.modules)
    # Since it is a local import "from vtx_app.producer import Director",
    # patching "vtx_app.producer.Director" should work if done before the import execution?
    # No, local import looks up vtx_app.producer.

    with patch("vtx_app.producer.Director") as MockDirector:
        instance = MockDirector.return_value
        result = runner.invoke(
            app,
            [
                "produce",
                "test_movie",
                "--concept",
                "A sci-fi short.",
                "--title",
                "Test Movie",
            ],
        )

        assert result.exit_code == 0
        MockDirector.assert_called_once()
        instance.produce.assert_called_once_with(
            slug="test_movie",
            concept="A sci-fi short.",
            title="Test Movie",
            auto_render=False,
        )
