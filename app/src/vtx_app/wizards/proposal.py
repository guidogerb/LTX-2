from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from rich import print

from vtx_app.config.settings import Settings
from vtx_app.integrations.civitai import CivitAIClient


@dataclass
class ProposalGenerator:
    settings: Settings

    def _client(self):
        from openai import OpenAI

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
                            "You are a movie producer. Analyze the user's movie idea."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Idea: {text}\n\nExtract title, slug, visual style keywords, and synopsis."
                        ),
                    },
                ],
                functions=[
                    {"name": "set_metadata", "parameters": schema}
                ],  # Using functions for older models compatibility or structured output
                function_call={"name": "set_metadata"},
                temperature=0.7,
            )
            # Adapt to whichever API style (Structured Outputs is preferred but check support)
            # The prompt "responses.create" was used in StoryBuilder, but standard chat completion is safer if sdk version varies.
            # actually StoryBuilder used client.responses.create which is very new. I will stick to tools/functions or json mode.

            args = json.loads(resp.choices[0].message.function_call.arguments)
            return args
        except Exception as e:
            print(f"[red]OpenAI analysis failed:[/red] {e}")
            # Fallback
            return {
                "title": "Untitled",
                "slug": "untitled_project",
                "logline": text[:100],
                "visual_style_keywords": [],
                "synopsis": text,
            }

    def create_proposal(self, concept_text: str) -> dict[str, Any]:
        import re
        from vtx_app.style_manager import StyleManager

        # Check for [style] tag
        style_match = re.match(r"^\[([\w\-_]+)\]\s*(.*)", concept_text, re.DOTALL)
        style_name = None
        if style_match:
            style_name = style_match.group(1)
            concept_text = style_match.group(2)  # Remove tag from concept
            print(f"[blue]Detected style preset:[/blue] {style_name}")

        print("[blue]Analyzing concept...[/blue]")
        analysis = self.analyze_concept(concept_text)

        # Inject style keywords if present
        extra_loras = []
        if style_name:
            mgr = StyleManager()
            keywords = mgr.get_style_keywords(style_name)
            if keywords:
                print(f"[dim]Injecting style keywords: {keywords}[/dim]")
                analysis["visual_style_keywords"] = keywords + analysis["visual_style_keywords"]
            
            # Load style-specific LoRAs to suggest
            style_data = mgr.load_style(style_name) or {}
            extra_loras = style_data.get("resources", {}).get("bundles", [])

        print(
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
                "Review this file. To create project, run: vtx projects create-from-plan proposal.yaml"
            ),
        }
        return proposal
