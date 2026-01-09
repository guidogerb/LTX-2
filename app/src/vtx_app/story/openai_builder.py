from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from openai import OpenAI

from vtx_app.project.layout import Project


@dataclass
class StoryBuilder:
    project: Project

    def _client(self) -> OpenAI:
        return OpenAI()

    def generate_outline(self) -> None:
        """
        Writes story/01_outline.yaml in a fixed schema.
        Uses OpenAI Structured Outputs (JSON schema) if OPENAI_API_KEY is set.
        """
        outline_path = self.project.root / "story" / "01_outline.yaml"
        brief_path = self.project.root / "story" / "00_brief.md"
        brief = brief_path.read_text() if brief_path.exists() else ""

        schema_path = Path(__file__).parent / "schemas" / "story.schema.json"
        schema = json.loads(schema_path.read_text())

        prompt = f"""You are a screenwriting assistant.
Create a 3-act outline (or use acts from the brief) for this project.
Return JSON that matches the provided JSON Schema exactly.

Project brief:
{brief}
"""

        # If no API key, keep existing stub
        try:
            client = self._client()
            resp = client.responses.create(
                model="gpt-5.2",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "Outline",
                        "schema": schema,
                        "strict": True,
                    }
                },
            )
            data = json.loads(resp.output_text)
            outline_path.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception:
            # Leave stub if API unavailable
            if not outline_path.exists():
                outline_path.write_text("version: 1\nacts: []\n")

    def generate_shotlist(self) -> None:
        shotlist_path = self.project.root / "story" / "04_shotlist.yaml"
        if not shotlist_path.exists():
            shotlist_path.write_text("version: 1\nscenes: []\n")

    def generate_clip_specs(self) -> None:
        """
        Placeholder: generates nothing by default. Extend to generate prompts/clips/*.yaml
        from outline + shotlist.
        """
        pass
