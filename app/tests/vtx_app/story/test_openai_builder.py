from unittest.mock import patch

import pytest
import yaml
from vtx_app.project.layout import Project
from vtx_app.story.openai_builder import StoryBuilder


@pytest.fixture
def project(tmp_path):
    # Setup minimal project structure
    p = tmp_path / "my_movie"
    p.mkdir()
    (p / "metadata.yaml").write_text("title: My Movie")
    (p / "project.env").touch()
    (p / "story").mkdir()
    (p / "prompts").mkdir()
    (p / "prompts" / "clips").mkdir()

    # Create dummy files required by generate_clip_specs
    (p / "prompts" / "style_bible.yaml").write_text("global_prefix: gp")
    (p / "prompts" / "characters.yaml").write_text("characters: {}")
    (p / "prompts" / "locations.yaml").write_text("locations: {}")
    (p / "prompts" / "loras.yaml").write_text("bundles: {}")

    return Project(root=p)


def test_generate_clip_specs_filters(project):
    """Test filtering by act and scene."""
    shotlist = {
        "scenes": [
            {
                "act": 1,
                "scene": 1,
                "shots": [{"clip_id": "A01_S01_SH001"}],
                "beats": [],
            },
            {
                "act": 1,
                "scene": 2,
                "shots": [{"clip_id": "A01_S02_SH001"}],
                "beats": [],
            },
            {
                "act": 2,
                "scene": 1,
                "shots": [{"clip_id": "A02_S01_SH001"}],
                "beats": [],
            },
        ]
    }
    (project.root / "story" / "04_shotlist.yaml").write_text(yaml.safe_dump(shotlist))

    builder = StoryBuilder(project=project)

    # Mock _call_structured to return clips matching the request context
    # We inspect messages to see which scene is being requested
    def side_effect(schema, messages):
        user_msg = messages[1]["content"]
        # Very simple heuristic to match the clip_id based on what's likely in the prompt
        if '"act": 1' in user_msg and '"scene": 1' in user_msg:
            return {"clips": [{"clip_id": "A01_S01_SH001", "title": "shot1"}]}
        if '"act": 1' in user_msg and '"scene": 2' in user_msg:
            return {"clips": [{"clip_id": "A01_S02_SH001", "title": "shot1"}]}
        if '"act": 2' in user_msg and '"scene": 1' in user_msg:
            return {"clips": [{"clip_id": "A02_S01_SH001", "title": "shot1"}]}
        return {"clips": []}

    with patch.object(builder, "_call_structured") as mock_call:
        mock_call.side_effect = side_effect

        # Test filtering act=1
        builder.generate_clip_specs(act=1)
        # Should call for scene 1 and 2 of act 1
        assert mock_call.call_count == 2
        mock_call.reset_mock()

        # Test filtering act=1, scene=2
        # Note: previous call created the files, so we must force overwrite to trigger generation again.
        builder.generate_clip_specs(act=1, scene=2, overwrite=True)
        assert mock_call.call_count == 1
        # Verify it was indeed scene 2
        kwargs = mock_call.call_args.kwargs
        messages = kwargs["messages"]
        assert '"scene": 2' in messages[1]["content"]


def test_generate_clip_specs_overwrite(project):
    """Test that overwrite flag controls whether we skip generation/writing."""
    shotlist = {"scenes": [{"act": 1, "scene": 1, "shots": [{"clip_id": "A01_S01_SH001"}]}]}
    (project.root / "story" / "04_shotlist.yaml").write_text(yaml.safe_dump(shotlist))

    # Pre-create the clip file. Note: The code searches glob f"{cid}__*.yaml"
    clip_file = project.root / "prompts" / "clips" / "A01_S01_SH001__existing.yaml"
    clip_file.write_text("original: content")

    builder = StoryBuilder(project=project)

    with patch.object(builder, "_call_structured") as mock_call:
        mock_call.return_value = {"clips": [{"clip_id": "A01_S01_SH001", "title": "new_title"}]}

        # Case 1: overwrite=False (default). Should detect existing file and SKIP the API call.
        builder.generate_clip_specs(overwrite=False)
        assert mock_call.call_count == 0
        assert clip_file.read_text() == "original: content"

        # Case 2: overwrite=True. Should CALL API and WRITE file.
        # Note: the code generates filename from title. "new_title" -> "A01_S01_SH001__new_title.yaml"
        # Since the filenames differ, it will write a NEW file, it won't strictly overwrite the old file
        # unless it renders to the exact same path.
        # However, the test here is about whether it PROCEEDS to generate found clips.

        builder.generate_clip_specs(overwrite=True)
        assert mock_call.call_count == 1

        new_file = project.root / "prompts" / "clips" / "A01_S01_SH001__new_title.yaml"
        assert new_file.exists()
        content = yaml.safe_load(new_file.read_text())
        assert content["clip_id"] == "A01_S01_SH001"
