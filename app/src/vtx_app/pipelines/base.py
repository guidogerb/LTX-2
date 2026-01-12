from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineCommand:
    module: str
    args: list[str]
    output_path: Path

    def as_subprocess(self) -> list[str]:
        return ["python", "-m", self.module, *self.args]
