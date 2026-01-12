from __future__ import annotations

import subprocess
from pathlib import Path


def concat_videos(inputs: list[Path], output: Path, force: bool = True) -> None:
    """
    Concatenates a list of video files into a single output file using the concat demuxer.
    """
    if not inputs:
        raise ValueError("No input files provided for concatenation")

    # Create the file list for ffmpeg
    list_file = output.with_suffix(".txt")
    lines = [f"file '{p.absolute().as_posix()}'" for p in inputs]
    list_file.write_text("\n".join(lines), encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(output),
    ]
    if force:
        cmd.insert(1, "-y")

    subprocess.check_call(cmd)

    # wrapper cleanup
    if list_file.exists():
        list_file.unlink()


def extract_frame(video_path: Path, output_image: Path, time: float = 0.0) -> None:
    """Extracts a single frame from a video at a specific time."""
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(time),
        "-i",
        str(video_path),
        "-vframes",
        "1",
        str(output_image),
    ]
    subprocess.check_call(cmd)
