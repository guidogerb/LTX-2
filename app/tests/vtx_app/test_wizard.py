from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from vtx_app.cli import app
from vtx_app.wizards.proposal import ProposalGenerator

runner = CliRunner()


@pytest.fixture
def mock_openai():
    with patch("vtx_app.wizards.proposal.ProposalGenerator._client") as mock:
        client = MagicMock()
        # Mocking the complex response structure is tedious, so we mock analyze_concept directly if possible,
        # but let's mock the keys needed for the method if we want to test logic.
        # Actually, let's just mock `analyze_concept` on the class for CLI tests.
        yield client


@pytest.fixture
def mock_analyze_concept(monkeypatch):
    def mock_return(self, text):
        return {
            "title": "Mock Movie",
            "slug": "mock_movie",
            "logline": "A mock movie logline.",
            "visual_style_keywords": ["cyberpunk"],
            "synopsis": "Full synopsis.",
        }

    monkeypatch.setattr(ProposalGenerator, "analyze_concept", mock_return)


@pytest.fixture
def mock_civitai(monkeypatch):
    from vtx_app.integrations.civitai import CivitAIClient

    def mock_search(self, query, limit=3):
        return [
            {
                "name": "CyberRisk",
                "url": "http://example.com",
                "download_url": "http://dl",
                "description": "desc",
            }
        ]

    monkeypatch.setattr(CivitAIClient, "search_loras", mock_search)


def test_propose_command(tmp_path, mock_analyze_concept, mock_civitai):
    # We need to run inside tmp_path so proposal.yaml is writable
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["projects", "propose", "A crazy idea"])
        assert result.exit_code == 0
        # Now defaults to {slug}_plan.yaml
        assert "Proposal written to mock_movie_plan.yaml" in result.stdout

        p = Path("mock_movie_plan.yaml")
        assert p.exists()
        data = yaml.safe_load(p.read_text())
        assert data["meta"]["title"] == "Mock Movie"
        assert len(data["resources"]["suggested_loras"]) > 0


def test_create_from_plan_command(tmp_path):
    # Setup
    plan_file = tmp_path / "my_plan.yaml"
    plan_data = {
        "meta": {"title": "Real Plan", "slug": "real_plan"},
        "story": {"brief": "Brief content"},
        "resources": {
            "suggested_loras": [{"name": "Lora1", "url": "u", "download_url": "d"}]
        },
    }
    plan_file.write_text(yaml.dump(plan_data))

    # We need to ensure we don't actually modify the real registry/projects folder
    # Mock settings to point to tmp_path
    with patch("vtx_app.project.loader.Settings.from_env") as mock_settings:
        m = MagicMock()
        m.projects_root = tmp_path / "projects"
        m.projects_root.mkdir()
        # Mock template root to avoid needing real templates
        with patch("vtx_app.project.loader.ProjectLoader._template_root") as mock_tmpl:
            tmpl_dir = tmp_path / "tmpl"
            tmpl_dir.mkdir(parents=True)
            (tmpl_dir / "metadata.yaml").write_text("slug: tmpl")

            # Ensure directories exist
            (tmpl_dir / "story").mkdir()
            (tmpl_dir / "prompts").mkdir()
            (tmpl_dir / "prompts" / "loras.yaml").write_text("bundles: {}\n")

            mock_tmpl.return_value = tmpl_dir

            mock_settings.return_value = m

            # Allow registry loading (mock it or use sqlite in memory?)
            # Registry.load() defaults to sqlite at app_home.
            # We should patch Registry.load
            with patch("vtx_app.registry.db.Registry.load") as mock_reg_load:
                mock_reg = MagicMock()
                mock_reg_load.return_value = mock_reg

                result = runner.invoke(
                    app, ["projects", "create-from-plan", str(plan_file)]
                )
                if result.exit_code != 0:
                    print(result.output)
                assert result.exit_code == 0, result.stdout

                # Verify project created
                proj_dir = m.projects_root / "real_plan"
                assert proj_dir.exists()

                # Check loras
                loras_file = proj_dir / "prompts" / "loras.yaml"
                assert loras_file.exists()
                loras = yaml.safe_load(loras_file.read_text())
                assert "civitai_candidates" in loras["bundles"]
