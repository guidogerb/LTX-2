from __future__ import annotations

import pytest
import yaml
from vtx_app.story.prompt_compiler import compile_prompt


@pytest.fixture
def mock_project(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    bible = {
        "global_prefix": "Global Prefix.",
        "global_negative": "Global Negative.",
        "profiles": {
            "default": {"prefix": "Default Profile.", "negative": "Default Negative."},
            "cyber": {"prefix": "Cyber Profile.", "negative": "Cyber Negative."},
        },
    }
    (prompts / "style_bible.yaml").write_text(yaml.safe_dump(bible))

    chars = {
        "characters": {
            "hero": {"description": "A brave hero."},
            "villain": {"description": "A dark villain."},
            "extra": (
                "Just a string desc"  # Handle legacy or simple string case? Current code expects dict.
            ),
        }
    }
    (prompts / "characters.yaml").write_text(yaml.safe_dump(chars))

    locs = {
        "locations": {
            "base": {"description": "Home base."},
            "moon": {"description": ""},  # Empty desc
        }
    }
    (prompts / "locations.yaml").write_text(yaml.safe_dump(locs))

    return tmp_path


def test_compile_simple(mock_project):
    clip_spec = {"prompt": {"positive": "A shot of the hero.", "negative": "blur"}}
    pack = compile_prompt(project_root=mock_project, clip_spec=clip_spec)

    assert "Global Prefix." in pack.positive
    assert "Default Profile." in pack.positive
    assert "A shot of the hero." in pack.positive
    assert "Global Negative." in pack.negative
    assert "Default Negative." in pack.negative
    assert "blur" in pack.negative


def test_compile_with_profile(mock_project):
    clip_spec = {
        "continuity": {"shared_prompt_profile": "cyber"},
        "prompt": {"positive": "Neon lights."},
    }
    pack = compile_prompt(project_root=mock_project, clip_spec=clip_spec)
    assert "Cyber Profile." in pack.positive
    assert "Default Profile." not in pack.positive


def test_compile_with_inserts(mock_project):
    clip_spec = {
        "continuity": {"characters": ["hero", "villain"], "locations": ["base"]},
        "prompt": {"positive": "Fight scene."},
    }
    pack = compile_prompt(project_root=mock_project, clip_spec=clip_spec)

    assert "CHARACTERS (locked for continuity):" in pack.positive
    assert "- hero: A brave hero." in pack.positive
    assert "- villain: A dark villain." in pack.positive
    assert "LOCATIONS (locked for continuity):" in pack.positive
    assert "- base: Home base." in pack.positive


def test_compile_missing_files(tmp_path):
    # Empty project without prompts folder
    clip_spec = {"prompt": {"positive": "foo"}}
    pack = compile_prompt(project_root=tmp_path, clip_spec=clip_spec)
    assert pack.positive == "foo"
    assert pack.negative == ""


def test_compile_empty_clip_spec(mock_project):
    pack = compile_prompt(project_root=mock_project, clip_spec={})
    assert "Global Prefix." in pack.positive
    assert pack.negative == "Global Negative.\nDefault Negative."


def test_compile_bad_continuity_keys(mock_project):
    clip_spec = {
        "continuity": {
            "characters": ["missing_char"],
            "locations": ["moon"],  # Has empty desc
        },
        "prompt": {"positive": "scene"},
    }
    pack = compile_prompt(project_root=mock_project, clip_spec=clip_spec)
    # missing keys are just added as "- key"
    assert "- missing_char" in pack.positive
    # Moon has empty desc, so just "- moon" wait code says: if desc: ... else: lines.append(f"- {k}")
    assert "- moon" in pack.positive
