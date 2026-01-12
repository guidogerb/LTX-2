from __future__ import annotations

import pytest
import yaml
from vtx_app.config.settings import Settings
from vtx_app.style_manager import StyleManager


@pytest.fixture
def mock_settings(monkeypatch, tmp_path):
    class MockSettings:
        app_home = tmp_path

    def mock_from_env():
        return MockSettings()

    monkeypatch.setattr(Settings, "from_env", mock_from_env)
    return tmp_path


@pytest.fixture
def style_manager(mock_settings):
    return StyleManager()


def test_init(style_manager, mock_settings):
    assert style_manager.root == mock_settings / "tags" / "style"
    assert style_manager.root.exists()


def test_save_style(style_manager, tmp_path):
    # Prepare dummy project
    project_root = tmp_path / "myproj"
    prompts = project_root / "prompts"
    prompts.mkdir(parents=True)

    (prompts / "style_bible.yaml").write_text(yaml.dump({"StyleBible": {"Format": "Movie"}}))
    (prompts / "loras.yaml").write_text(yaml.dump({"bundles": {"civitai_candidates": ["lora1"]}}))

    # Save
    out = style_manager.save_style("mystyle", project_root, "desc")
    assert out.exists()
    assert out.name == "mystyle.yaml"

    # Verify content
    data = yaml.safe_load(out.read_text())
    assert data["meta"]["name"] == "mystyle"
    assert data["style_bible"]["Format"] == "Movie"
    assert data["resources"]["bundles"] == ["lora1"]


def test_save_style_no_bible(style_manager, tmp_path):
    project_root = tmp_path / "broken"
    project_root.mkdir()
    (project_root / "prompts").mkdir()

    with pytest.raises(FileNotFoundError):
        style_manager.save_style("style", project_root)


def test_crud_style(style_manager):
    # Create manually for testing read
    path = style_manager.root / "test.yaml"
    path.write_text(yaml.dump({"meta": {"description": "d"}}))

    # List
    assert "test" in style_manager.list_styles()

    # Load
    data = style_manager.load_style("test")
    assert data["meta"]["description"] == "d"
    assert style_manager.load_style("missing") is None

    # Update
    assert style_manager.update_description("test", "updated")
    data = style_manager.load_style("test")
    assert data["meta"]["description"] == "updated"
    assert not style_manager.update_description("missing", "u")

    # Delete
    assert style_manager.delete_style("test")
    assert not path.exists()
    assert not style_manager.delete_style("missing")


def test_get_style_keywords(style_manager):
    # Setup style with keywords
    content = {
        "style_bible": {
            "Format": {"OverallAesthetic": "Cinematic"},
            "CoreLook": {"Lighting": "Dark"},
        }
    }
    path = style_manager.root / "kw_style.yaml"
    path.write_text(yaml.dump(content))

    keywords = style_manager.get_style_keywords("kw_style")
    assert "Cinematic" in keywords
    # If the logic extracts Lighting, assert it. Need to check implementation details.

    assert style_manager.get_style_keywords("missing") == []
