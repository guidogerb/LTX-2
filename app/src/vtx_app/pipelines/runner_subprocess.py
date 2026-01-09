from __future__ import annotations

import subprocess
from rich import print
from vtx_app.pipelines.base import PipelineCommand


def run(cmd: PipelineCommand) -> None:
    cmdline = cmd.as_subprocess()
    print("[cyan]RUN[/cyan] " + " ".join(cmdline))
    subprocess.check_call(cmdline)
