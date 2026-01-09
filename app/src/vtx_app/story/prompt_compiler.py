from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class PromptPack:
    positive: str
    negative: str

def compile_prompt(*, project_root: Path, clip_spec: dict) -> PromptPack:
    """
    Compile final prompts by merging:
      - prompts/style_bible.yaml (global + selected profile)
      - characters.yaml + locations.yaml inserts (optional)
      - clip_spec.prompt.positive/negative

    This is intentionally simple; extend as needed.
    """
    bible = yaml.safe_load((project_root/"prompts/style_bible.yaml").read_text())
    profile_name = clip_spec["continuity"]["shared_prompt_profile"]
    prof = bible.get("profiles", {}).get(profile_name, {})

    prefix = (bible.get("global_prefix","") + "\n" + prof.get("prefix","")).strip()
    neg = (bible.get("global_negative","") + "\n" + prof.get("negative","")).strip()

    clip_pos = clip_spec["prompt"]["positive"].strip()
    clip_neg = (clip_spec["prompt"].get("negative") or "").strip()

    positive = "\n".join([p for p in [prefix, clip_pos] if p]).strip()
    negative = "\n".join([p for p in [neg, clip_neg] if p]).strip()

    return PromptPack(positive=positive, negative=negative)
