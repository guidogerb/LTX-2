from unittest.mock import patch

import pytest
import yaml
from vtx_app.project.layout import Project
from vtx_app.render.assembler import Assembler


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "story").mkdir()
    (root / "prompts" / "clips").mkdir(parents=True)
    (root / "renders" / "clips").mkdir(parents=True)
    return Project(root=root)


def test_assemble(project):
    # Setup shotlist
    shotlist = {"scenes": [{"shots": [{"clip_id": "c1"}, {"clip_id": "c2"}]}]}
    (project.root / "story" / "04_shotlist.yaml").write_text(yaml.safe_dump(shotlist))

    # Setup clips specs and rendered files
    # c1: exists
    (project.root / "prompts" / "clips" / "c1__shot1.yaml").write_text(
        yaml.safe_dump({"outputs": {"mp4": "renders/clips/c1.mp4"}})
    )
    (project.root / "renders" / "clips" / "c1.mp4").touch()

    # c2: missing render
    (project.root / "prompts" / "clips" / "c2__shot2.yaml").write_text(
        yaml.safe_dump({"outputs": {"mp4": "renders/clips/c2.mp4"}})
    )
    # c2.mp4 not created

    asm = Assembler(project)

    with patch("vtx_app.render.assembler.concat_videos") as mock_concat:
        asm.assemble("out.mp4")

        # Should have called concat with only c1
        assert mock_concat.called
        args = mock_concat.call_args[0]
        files = args[0]
        assert len(files) == 1
        assert files[0].name == "c1.mp4"
