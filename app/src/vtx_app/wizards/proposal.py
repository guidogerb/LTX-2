from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from rich import print as rich_print

from vtx_app.config.settings import Settings
from vtx_app.integrations.civitai import CivitAIClient
from vtx_app.style_manager import StyleManager
from vtx_app.tags_manager import TagManager


@dataclass
class ProposalGenerator:
    settings: Settings

    def _client(self):
        return OpenAI()

    def analyze_concept(self, text: str) -> dict[str, Any]:
        """
        Analyze concept text to extract metadata and keywords.
        """
        client = self._client()

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "slug": {"type": "string", "description": "short_snake_case_id"},
                "logline": {"type": "string"},
                "visual_style_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Keywords for finding LoRAs (e.g. 'anime', 'cyberpunk', 'claymation')"
                    ),
                },
                "synopsis": {"type": "string", "description": "Expanded plot summary"},
            },
            "required": [
                "title",
                "slug",
                "logline",
                "visual_style_keywords",
                "synopsis",
            ],
            "additionalProperties": False,
        }

        try:
            resp = client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a movie producer. Analyze the user's movie idea. "
                            "Return JSON that matches the provided JSON Schema exactly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Idea: {text}\n\nExtract title, slug, visual style keywords, and synopsis."
                        ),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "proposal_metadata",
                        "strict": True,
                        "schema": schema,
                    },
                },
                temperature=0.7,
            )

            content = resp.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            args = json.loads(content)
            return args
        except Exception as e:
            rich_print(f"[red]OpenAI analysis failed:[/red] {e}")
            # Fallback
            return {
                "title": "Untitled",
                "slug": "untitled_project",
                "logline": text[:100],
                "visual_style_keywords": [],
                "synopsis": text,
            }

    def create_proposal(self, concept_text: str) -> dict[str, Any]:

        # 1. Expand Tags
        # This replaces [group_tag] with the content from the yaml 'prompt' field.
        tm = TagManager()
        concept_text = tm.process_prompt(concept_text)

        # 2. Check for [style] or [movie-style] tag for setting global preset
        # We accept [style_name] or [movie-style_name].
        style_name = None

        # Regex to find [style_SOMETHING] or [movie-style_SOMETHING] anywhere
        # These tags might remain if they had no 'prompt' content in the YAML.
        style_matches = list(
            re.finditer(r"\[(?:movie-)?style_([\w\-]+)\]", concept_text)
        )

        if style_matches:
            # Take the first one as the primary preset
            match = style_matches[0]
            style_name = match.group(1)
            rich_print(f"[blue]Detected style preset:[/blue] {style_name}")

            # Remove all style tags from text so they don't pollute the story analysis
            concept_text = re.sub(
                r"\[(?:movie-)?style_[\w\-]+\]", "", concept_text
            ).strip()

        # Legacy fallback: check for [style] at start of string if no style found yet
        if not style_name:
            style_match = re.match(r"^\[([\w\-_]+)\]\s*(.*)", concept_text, re.DOTALL)
            if style_match:
                potential_name = style_match.group(1)
                # Verify it exists as a style
                mgr = StyleManager()
                if mgr.load_style(potential_name):
                    style_name = potential_name
                    concept_text = style_match.group(2)
                    rich_print(
                        f"[blue]Detected legacy style preset:[/blue] {style_name}"
                    )

        rich_print("[blue]Analyzing concept...[/blue]")
        analysis = self.analyze_concept(concept_text)

        # Inject style keywords if present
        extra_loras = []
        if style_name:
            mgr = StyleManager()
            keywords = mgr.get_style_keywords(style_name)
            if keywords:
                rich_print(f"[dim]Injecting style keywords: {keywords}[/dim]")
                analysis["visual_style_keywords"] = (
                    keywords + analysis["visual_style_keywords"]
                )

            # Load style-specific LoRAs to suggest
            style_data = mgr.load_style(style_name) or {}
            extra_loras = style_data.get("resources", {}).get("bundles", [])

        rich_print(
            f"[blue]Searching CivitAI for styles: {analysis['visual_style_keywords']}...[/blue]"
        )
        civitai = CivitAIClient()
        suggested_loras = []
        # Search for first few keywords
        for kw in analysis["visual_style_keywords"][:2]:
            results = civitai.search_loras(kw, limit=2)
            suggested_loras.extend(results)

        # Merge style extras
        # We put style extras first so they take precedence in user attention
        suggested_loras = extra_loras + suggested_loras

        proposal = {
            "meta": {
                "title": analysis["title"],
                "slug": analysis["slug"],
                "logline": analysis["logline"],
            },
            "story": {"brief": analysis["synopsis"]},
            "resources": {"suggested_loras": suggested_loras},
            "instructions": (
                "Review this file. To create project, run: vtx projects create-from-plan proposal.yaml"
            ),
        }

        if style_name:
            proposal["meta"]["style_preset"] = style_name

        return proposal
