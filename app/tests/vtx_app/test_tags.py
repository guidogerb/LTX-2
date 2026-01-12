from __future__ import annotations

import pytest
from typer.testing import CliRunner
from vtx_app.config.settings import Settings
from vtx_app.tags_commands import tags_app
from vtx_app.tags_manager import TagManager

runner = CliRunner()


@pytest.fixture
def mock_settings(monkeypatch, tmp_path):
    # Mock Settings.from_env() to return a simplified object with app_home
    class MockSettings:
        app_home = tmp_path

    def mock_from_env():
        return MockSettings()

    monkeypatch.setattr(Settings, "from_env", mock_from_env)
    return tmp_path


@pytest.fixture
def tag_manager(mock_settings):
    return TagManager()


def test_tag_manager_init(tag_manager, mock_settings):
    assert (mock_settings / "tags").exists()
    assert tag_manager.root == mock_settings / "tags"


def test_list_empty(tag_manager):
    assert tag_manager.list_groups() == []
    assert tag_manager.list_tags() == {}


def test_crud_tags(tag_manager):
    # Create
    content = {"prompt": "foo bar", "meta": {"description": "desc"}}
    tag_manager.save_tag("group-a", "tag-1", content)

    assert tag_manager.list_groups() == ["group-a"]
    assert tag_manager.list_tags() == {"group-a": ["tag-1"]}

    # Read
    loaded = tag_manager.load_tag("group-a", "tag-1")
    assert loaded == content

    # Update description
    assert tag_manager.update_description("group-a", "tag-1", "new desc")
    loaded = tag_manager.load_tag("group-a", "tag-1")
    assert loaded["meta"]["description"] == "new desc"

    # Missing
    assert tag_manager.load_tag("group-a", "missing") is None
    assert not tag_manager.update_description("group-a", "missing", "d")

    # List specific group
    assert tag_manager.list_tags("group-a") == {"group-a": ["tag-1"]}
    with pytest.raises(FileNotFoundError):
        tag_manager.list_tags("group-b")


def test_process_prompt(tag_manager):
    # Setup tags
    tag_manager.save_tag("style", "noir", {"prompt": "black and white, high contrast"})
    tag_manager.save_tag("shot", "wide", {"prompt": "wide angle shot"})
    tag_manager.save_tag("meta", "only-desc", {"meta": {"description": "just description"}})
    tag_manager.save_tag("empty", "void", {})

    # Single replacement
    text = "A scene in [style_noir] style."
    processed = tag_manager.process_prompt(text)
    assert processed == "A scene in black and white, high contrast style."

    # Multiple replacements
    text = "[shot_wide] of a city, [style_noir]."
    processed = tag_manager.process_prompt(text)
    assert processed == "wide angle shot of a city, black and white, high contrast."

    # Dash in names
    tag_manager.save_tag("my-group", "my-tag", {"prompt": "dashed"})
    text = "Use [my-group_my-tag]."
    processed = tag_manager.process_prompt(text)
    assert processed == "Use dashed."

    # Missing tag - keep original
    text = "Use [style_missing]."
    processed = tag_manager.process_prompt(text)
    assert processed == "Use [style_missing]."

    # Missing prompt, use description
    text = "Use [meta_only-desc]."
    processed = tag_manager.process_prompt(text)
    assert processed == "Use just description."

    # No content
    text = "Use [empty_void]."
    processed = tag_manager.process_prompt(text)
    assert processed == "Use [empty_void]."


def test_cli_list(mock_settings, tag_manager):
    tag_manager.save_tag("group-a", "tag-1", {"meta": {"description": "desc1"}})

    result = runner.invoke(tags_app, ["list-groups"])
    assert result.exit_code == 0
    assert "group-a" in result.stdout

    result = runner.invoke(tags_app, ["list-all"])
    assert result.exit_code == 0
    assert "group-a" in result.stdout
    assert "tag-1" in result.stdout
    assert "desc1" in result.stdout


def test_cli_update(mock_settings, tag_manager):
    tag_manager.save_tag("g", "t", {"meta": {"description": "old"}})

    # Success
    result = runner.invoke(tags_app, ["update-desc", "g", "t", "new"])
    assert result.exit_code == 0
    assert "Updated description" in result.stdout

    # Verify
    assert tag_manager.load_tag("g", "t")["meta"]["description"] == "new"

    # Fail
    result = runner.invoke(tags_app, ["update-desc", "g", "missing", "new"])
    assert result.exit_code == 0
    assert "not found" in result.stdout
