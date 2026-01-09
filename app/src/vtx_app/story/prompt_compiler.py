from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PromptPack:
    positive: str
    negative: str


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        return {}
    return data


def compile_prompt(*, project_root: Path, clip_spec: dict[str, Any]) -> PromptPack:
    """
    Compile final prompts by merging:
      - prompts/style_bible.yaml (global + selected profile)
      - prompts/characters.yaml inserts (optional)
      - prompts/locations.yaml inserts (optional)
      - clip-specific positive/negative

    The clip's prompt should *not* restate the global style bible; keep it shot-specific.
    """
    bible = _load_yaml(project_root / "prompts" / "style_bible.yaml")
    profile_name = ((clip_spec.get("continuity") or {}).get("shared_prompt_profile")) or "default"
    prof = (bible.get("profiles", {}) or {}).get(profile_name, {}) or {}

    prefix = (str(bible.get("global_prefix", "")) + "\n" + str(prof.get("prefix", ""))).strip()
    neg = (str(bible.get("global_negative", "")) + "\n" + str(prof.get("negative", ""))).strip()

    # Character/location inserts (keeps identity + setting consistent without repeating in every clip prompt)
    chars_doc = _load_yaml(project_root / "prompts" / "characters.yaml")
    locs_doc = _load_yaml(project_root / "prompts" / "locations.yaml")
    chars = chars_doc.get("characters", {}) if isinstance(chars_doc.get("characters", {}), dict) else {}
    locs = locs_doc.get("locations", {}) if isinstance(locs_doc.get("locations", {}), dict) else {}

    continuity = clip_spec.get("continuity") or {}
    char_keys = continuity.get("characters") or []
    loc_keys = continuity.get("locations") or []

    inserts: list[str] = []

    if isinstance(char_keys, list) and char_keys:
        lines = []
        for k in char_keys:
            entry = chars.get(k, {})
            if isinstance(entry, dict):
                desc = entry.get("description")
            else:
                desc = None
            if desc:
                lines.append(f"- {k}: {desc}")
            else:
                lines.append(f"- {k}")
        inserts.append("CHARACTERS (locked for continuity):\n" + "\n".join(lines))

    if isinstance(loc_keys, list) and loc_keys:
        lines = []
        for k in loc_keys:
            entry = locs.get(k, {})
            if isinstance(entry, dict):
                desc = entry.get("description")
            else:
                desc = None
            if desc:
                lines.append(f"- {k}: {desc}")
            else:
                lines.append(f"- {k}")
        inserts.append("LOCATIONS (locked for continuity):\n" + "\n".join(lines))

    insert_block = "\n\n".join(inserts).strip()

    clip_prompt = clip_spec.get("prompt") or {}
    clip_pos = str(clip_prompt.get("positive", "")).strip()
    clip_neg = str(clip_prompt.get("negative", "") or "").strip()

    positive = "\n\n".join([p for p in [prefix, insert_block, clip_pos] if p]).strip()
    negative = "\n\n".join([p for p in [neg, clip_neg] if p]).strip()

    return PromptPack(positive=positive, negative=negative)
