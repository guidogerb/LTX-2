from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache

_FLAG_RE = re.compile(r"(--[a-zA-Z0-9][a-zA-Z0-9_-]*)")


@dataclass(frozen=True)
class PipelineCapabilities:
    module: str
    flags: set[str]


@lru_cache(maxsize=64)
def detect_capabilities(module: str) -> PipelineCapabilities:
    """
    Best-effort capability detection by calling:
        python -m <module> --help

    We then regex-scan for flags like --negative-prompt, --width, --num-frames, etc.

    This keeps the app resilient against changes in LTX-2 pipeline CLI args
    without hardcoding every option.

    If detection fails, flags will be empty and the renderer will fall back to the
    minimal required args.
    """
    try:
        out = subprocess.check_output(
            ["python", "-m", module, "--help"],
            stderr=subprocess.STDOUT,
            text=True,
        )
        flags = set(_FLAG_RE.findall(out))
        return PipelineCapabilities(module=module, flags=flags)
    except Exception:
        return PipelineCapabilities(module=module, flags=set())


def first_supported(cap: PipelineCapabilities, *candidates: str) -> str | None:
    """
    Return the first candidate flag supported by the module, else None.
    """
    for c in candidates:
        if c in cap.flags:
            return c
    return None
