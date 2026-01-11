from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml
from rich import print

from vtx_app.config.settings import Settings


@dataclass
class TagManager:
    """Manages system-wide tags organized by groups."""

    def __init__(self):
        self.root = Settings.from_env().app_home / "tags"
        self.root.mkdir(parents=True, exist_ok=True)

    def list_groups(self) -> list[str]:
        """Returns a list of all tag groups."""
        return sorted(
            [
                d.name
                for d in self.root.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]
        )

    def list_tags(self, group: str | None = None) -> dict[str, list[str]]:
        """
        Returns tags organized by group.
        If group is specified, only returns that group.
        """
        groups = [group] if group else self.list_groups()
        result = {}

        for g in groups:
            group_dir = self.root / g
            if not group_dir.exists():
                if group:
                    raise FileNotFoundError(f"Group '{g}' not found.")
                continue

            tags = sorted([f.stem for f in group_dir.glob("*.yaml")])
            result[g] = tags

        return result

    def get_tag_path(self, group: str, tag: str) -> Path:
        return self.root / group / f"{tag}.yaml"

    def load_tag(self, group: str, tag: str) -> Optional[dict[str, Any]]:
        path = self.get_tag_path(group, tag)
        if not path.exists():
            return None
        return yaml.safe_load(path.read_text()) or {}

    def save_tag(self, group: str, tag: str, content: dict[str, Any]) -> None:
        group_dir = self.root / group
        group_dir.mkdir(parents=True, exist_ok=True)
        path = group_dir / f"{tag}.yaml"
        path.write_text(yaml.safe_dump(content, sort_keys=False))

    def update_description(self, group: str, tag: str, description: str) -> bool:
        data = self.load_tag(group, tag)
        if data is None:
            return False

        if "meta" not in data:
            data["meta"] = {}
        data["meta"]["description"] = description
        self.save_tag(group, tag, data)
        return True

    def process_prompt(self, text: str) -> str:
        """
        Replaces [group_tag] occurrences in the text with the tag content.
        For 'style' tags, we might leave them if they are handled specially,
        or we can expand them here too.

        The user asked for: [movie-style_pixar] -> implies we expand it?
        Or maybe style tags are special.
        But 'tags can be placed in the descriptions... encapsilate large instructions'.
        So replacement is the goal.
        """
        # Regex for [group_tag] or [group-tag]
        # User defined format: [group_name-tag_name] or [group_name_tag_name]
        # User examples: [movie-duration_ten-minutes], [style_pixar]
        # It seems the separator between group and tag is '_' in user examples.
        # But group names can have dashes: 'movie-duration'.

        pattern = re.compile(r"\[([\w\-]+)_([\w\-]+)\]")

        def replace(match):
            group = match.group(1)
            tag = match.group(2)

            data = self.load_tag(group, tag)
            if not data:
                # If not found, check if it's a legacy style (style-name) -> style_name
                # If user typed [style_pixar], group=style, tag=pixar.
                # If we moved styles to tags/style/pixar.yaml, then load_tag('style', 'pixar') works.
                print(
                    f"[yellow]Warning: Tag [{group}_{tag}] not found used in prompt.[/yellow]"
                )
                return match.group(0)  # Keep original text if fail

            # What to return?
            # 'prompt' field? 'description'?
            # If it's a style file (moved from old system), it has 'style_bible'.
            # It might not have a 'prompt' field.
            # If it has a 'prompt' field, use that.
            # If not, maybe use 'meta' -> 'description'?

            replacement = data.get("prompt")
            if not replacement:
                # Fallback to description if prompt is missing
                replacement = data.get("meta", {}).get("description")

            if replacement:
                return replacement

            return match.group(0)

        return pattern.sub(replace, text)
