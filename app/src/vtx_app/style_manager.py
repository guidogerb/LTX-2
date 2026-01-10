from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from vtx_app.config.settings import Settings


@dataclass
class StyleManager:
    """Manages reusable visual styles stored in _global/styles."""

    def __init__(self):
        self.root = Settings.from_env().app_home / "styles"
        self.root.mkdir(parents=True, exist_ok=True)

    def save_style(self, name: str, project_root: Path) -> Path:
        """Extracts style config from a project and saves it as a style preset."""
        # Load source files
        style_bible_path = project_root / "prompts" / "style_bible.yaml"
        loras_path = project_root / "prompts" / "loras.yaml"

        if not style_bible_path.exists():
            raise FileNotFoundError(f"Project has no style bible at {style_bible_path}")

        style_bible = yaml.safe_load(style_bible_path.read_text()) or {}
        loras = {}
        if loras_path.exists():
            loras = yaml.safe_load(loras_path.read_text()) or {}

        # Construct style definition
        # We capture the main StyleBible content and the CivitAI bundles
        style_data = {
            "meta": {
                "name": name,
                "source_project": project_root.name,
            },
            "style_bible": style_bible.get("StyleBible", {}),
            "resources": {
                "bundles": (loras.get("bundles") or {}).get("civitai_candidates", [])
            },
        }

        out_path = self.root / f"{name}.yaml"
        out_path.write_text(yaml.safe_dump(style_data, sort_keys=False))
        return out_path

    def load_style(self, name: str) -> Optional[dict[str, Any]]:
        """Loads a style by name."""
        path = self.root / f"{name}.yaml"
        if not path.exists():
            return None
        return yaml.safe_load(path.read_text())

    def list_styles(self) -> list[str]:
        """Returns list of available style names."""
        return sorted([p.stem for p in self.root.glob("*.yaml")])

    def get_style_keywords(self, name: str) -> list[str]:
        """Extracts keywords from a style for searching/prompting."""
        data = self.load_style(name)
        if not data:
            return []

        bible = data.get("style_bible", {})
        fmt = bible.get("Format", {})
        look = bible.get("CoreLook", {})

        keywords = []
        if fmt.get("OverallAesthetic"):
            keywords.append(fmt["OverallAesthetic"])
        if look.get("Rendering", {}).get("Style"):
            keywords.append(look["Rendering"]["Style"])

        return keywords
