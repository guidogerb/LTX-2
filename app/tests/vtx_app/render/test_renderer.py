from unittest.mock import MagicMock, patch

import pytest
import yaml

from vtx_app.project.layout import Project
from vtx_app.render.renderer import RenderController


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "prompts" / "clips").mkdir(parents=True)
    (root / "metadata.yaml").write_text("project_id: p1")
    return Project(root=root)


def test_render_clip_validation(project):
    # Invalid clip (missing render section)
    clip_id = "c1"
    (project.root / "prompts" / "clips" / f"{clip_id}.yaml").write_text(
        yaml.safe_dump({"clip_id": "c1", "prompt": {"positive": "foo"}})
    )

    registry = MagicMock()
    controller = RenderController(project=project, registry=registry)

    # Needs to mock compile_prompt and run?
    # Validation happens before compile_prompt

    with pytest.raises(Exception) as excinfo:
        controller.render_clip(clip_id=clip_id)

    # Should be validation error
    assert "render" in str(excinfo.value) or "validation" in str(excinfo.value).lower()


@patch("vtx_app.render.renderer.run")
@patch("vtx_app.render.renderer.compile_prompt")
@patch(
    "vtx_app.render.renderer.validate_clip_spec"
)  # Mock validation to skip schema check for input test (or provide valid spec)
def test_render_clip_inputs(mock_val, mock_compile, mock_run, project):
    clip_id = "c2"

    # Valid clip with inputs
    clip_data = {
        "clip_id": "c2",
        "prompt": {"positive": "foo"},
        "render": {
            "pipeline": "ti2vid_two_stages",
            "fps": 24,
            "width": 512,
            "height": 512,
            "seed": 0,
        },
        "inputs": {"reference_image": "assets/ref.png"},
        "outputs": {"mp4": "out.mp4"},
    }
    (project.root / "prompts" / "clips" / f"{clip_id}.yaml").write_text(
        yaml.safe_dump(clip_data)
    )

    # Setup compile return
    mock_compile.return_value = MagicMock(positive="foo", negative=None)

    registry = MagicMock()
    controller = RenderController(project=project, registry=registry)

    # Need to mock capabilities because first_supported detects flags
    with patch("vtx_app.render.renderer.detect_capabilities") as mock_cap:
        # Mock cap to return flags
        mock_cap.return_value = MagicMock(
            flags={"--image", "--prompt", "--output-path"}
        )

        controller.render_clip(clip_id=clip_id)

        # Verify run called with image arg
        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        args = cmd.args
        assert "--image" in args
        assert str(project.root / "assets/ref.png") in args
