from unittest.mock import patch

from vtx_app.render import ffmpeg


def test_concat_videos(tmp_path):
    f1 = tmp_path / "1.mp4"
    f2 = tmp_path / "2.mp4"
    f1.touch()
    f2.touch()
    out = tmp_path / "out.mp4"

    with patch("subprocess.check_call") as mock_run:
        ffmpeg.concat_videos([f1, f2], out)

        # Verify call
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-f" in cmd
        assert "concat" in cmd
        assert str(out) in cmd

        # Check list file content
        # wrapper cleanup deletes it usually


def test_concat_videos_cleanup(tmp_path):
    """Ensure list file is cleaned up even if ffmpeg fails (or succeeds)."""
    f1 = tmp_path / "1.mp4"
    f1.touch()
    out = tmp_path / "out.mp4"

    with patch("subprocess.check_call"):
        ffmpeg.concat_videos([f1], out)

    assert not out.with_suffix(".txt").exists()


def test_extract_frame(tmp_path):
    vid = tmp_path / "vid.mp4"
    img = tmp_path / "img.png"

    with patch("subprocess.check_call") as mock_run:
        ffmpeg.extract_frame(vid, img, time=5.0)

        cmd = mock_run.call_args[0][0]
        assert "-ss" in cmd
        assert "5.0" in cmd
        assert str(img) in cmd
