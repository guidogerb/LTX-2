from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_READ_HOLD_KEYWORDS = [
    "read",
    "readable",
    "inscription",
    "plaque",
    "lettering",
    "caption",
    "text on",
    "clearly readable",
]

_SLOW_KEYWORDS = [
    "slow",
    "lingers",
    "hold",
    "pensive",
    "smoke spirals",
    "volumetric",
    "eerie",
    "quiet",
]


def estimate_seconds(clip_spec: dict[str, Any]) -> float:
    """
    Heuristic duration estimator.

    Goal: default to 'as short as possible while covering the content well' while letting
    the content (story beats + prompt text) influence duration.

    The renderer will clamp the final frames to LTX_MAX_FRAMES and max_seconds.
    """
    render = clip_spec.get("render", {})
    dur = render.get("duration", {}) or {}

    mode = dur.get("mode", "auto")
    if mode == "fixed" and isinstance(dur.get("seconds"), (int, float)):
        return float(dur["seconds"])

    beats = clip_spec.get("story_beats") or []
    if not isinstance(beats, list):
        beats = []

    # Base + per-beat pacing
    base = 1.6
    per_beat = 1.1
    seconds = base + per_beat * max(0, len(beats))

    # Clamp to min/max from spec
    min_s = float(dur.get("min_seconds", 0) or 0)
    max_s = float(dur.get("max_seconds", 15) or 15)

    # Keyword nudges (try to respect 'hold long enough to read' moments)
    prompt_pos = (clip_spec.get("prompt") or {}).get("positive") or ""
    prompt_lc = prompt_pos.lower()

    if any(k in prompt_lc for k in _READ_HOLD_KEYWORDS):
        seconds = max(seconds, 3.2)

    if any(k in prompt_lc for k in _SLOW_KEYWORDS):
        seconds = max(seconds, 2.8)

    # If there is dialogue, allow a bit more time
    # (dialogue may be embedded in prompt text; we look for quotes)
    if re.search(r"\".+?\"", prompt_pos) or re.search(r"'[^']+'", prompt_pos):
        seconds = max(seconds, 4.0)

    # Clamp
    if min_s > 0:
        seconds = max(seconds, min_s)
    seconds = min(seconds, max_s)

    # Never generate 0-length clips
    return max(0.5, seconds)
