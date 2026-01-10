from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from vtx_app.project.layout import Project


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _slugify(text: str) -> str:
    import re

    s = (text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "untitled"


@dataclass
class StoryBuilder:
    project: Project

    def _client(self):
        # OPENAI_API_KEY is read automatically by the official SDK when present.
        # If missing, OpenAI() will raise.
        from openai import OpenAI

        return OpenAI()

    def _call_structured(
        self, *, schema: dict[str, Any], messages: list[dict[str, str]]
    ) -> dict[str, Any]:
        s = self.project.settings()
        client = self._client()
        resp = client.responses.create(
            model=s.openai_model,
            input=messages,
            temperature=s.openai_temperature,
            max_output_tokens=s.openai_max_output_tokens,
            text={"format": {"type": "json_schema", "strict": True, "schema": schema}},
        )
        return json.loads(resp.output_text)

    def generate_outline(self) -> None:
        """
        Writes story/01_outline.yaml in a fixed schema.
        Uses OpenAI Structured Outputs if OPENAI_API_KEY is set.
        """
        outline_path = self.project.root / "story" / "01_outline.yaml"
        brief_path = self.project.root / "story" / "00_brief.md"
        brief = brief_path.read_text() if brief_path.exists() else ""

        schema_path = Path(__file__).parent / "schemas" / "story.schema.json"
        schema = json.loads(schema_path.read_text())

        system = (
            "You are a screenwriting assistant. Create a clear, filmable outline. "
            "Return JSON that matches the provided JSON Schema exactly."
        )
        user = f"""Project brief:
{brief}

Write an outline with acts -> scenes -> beats.
Use act/scene numbering starting at 1.
Keep beats short and visual.
"""

        try:
            data = self._call_structured(
                schema=schema,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            outline_path.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception:
            # Leave stub if API unavailable
            if not outline_path.exists():
                outline_path.write_text("version: 1\nacts: []\n")

    def generate_treatment(self) -> None:
        """Writes story/02_treatment.md from outline/brief."""
        treatment_path = self.project.root / "story" / "02_treatment.md"
        outline_path = self.project.root / "story" / "01_outline.yaml"
        brief_path = self.project.root / "story" / "00_brief.md"

        outline = outline_path.read_text() if outline_path.exists() else ""
        brief = brief_path.read_text() if brief_path.exists() else ""

        schema_path = Path(__file__).parent / "schemas" / "treatment.schema.json"
        schema = json.loads(schema_path.read_text())

        system = "You are a screenwriter. Write a detailed film treatment (prose format) based on the outline."
        user = f"Brief:\n{brief}\n\nOutline:\n{outline}\n\nWrite the treatment."

        try:
            data = self._call_structured(
                schema=schema,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            content = data.get("content", "")
            title = data.get("title", "Treatment")
            treatment_path.write_text(f"# {title}\n\n{content}")
        except Exception:
            if not treatment_path.exists():
                treatment_path.write_text("# Treatment\n\n(Pending)\n")

    def generate_shotlist(self) -> None:
        """
        Writes story/04_shotlist.yaml in a fixed schema.
        Uses outline + treatment/screenplay (if present).
        """
        shotlist_path = self.project.root / "story" / "04_shotlist.yaml"
        outline_path = self.project.root / "story" / "01_outline.yaml"
        treatment_path = self.project.root / "story" / "02_treatment.md"

        outline = outline_path.read_text() if outline_path.exists() else ""
        treatment = treatment_path.read_text() if treatment_path.exists() else ""

        schema_path = Path(__file__).parent / "schemas" / "shotlist.schema.json"
        schema = json.loads(schema_path.read_text())

        # Provide available keys for locations/characters so the model uses consistent identifiers.
        chars = _load_yaml(self.project.root / "prompts" / "characters.yaml").get(
            "characters", {}
        )
        locs = _load_yaml(self.project.root / "prompts" / "locations.yaml").get(
            "locations", {}
        )

        system = (
            "You are a director + cinematographer assistant. "
            "Create a practical shotlist that can be rendered as short clips (<= 15s each). "
            "Return JSON matching the schema exactly. Do not add extra keys."
        )
        user = f"""Outline (YAML):
{outline}

Treatment (optional):
{treatment}

Available character keys (use these strings in 'characters'):
{list(chars.keys())}

Available location keys (use these strings in 'locations' and 'location_key'):
{list(locs.keys())}

Create a shotlist broken down by scenes.
For each scene:
- act, scene, slug, title, summary, location_key, time_of_day, beats
For each shot:
- include clip_id in the format A## _ S## _ SH### (no spaces)
- keep descriptions visual and specific
- 'duration_hint_seconds' may be 0 for auto pacing, or a small number if necessary (e.g. readable plaque)
"""

        try:
            data = self._call_structured(
                schema=schema,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            shotlist_path.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception:
            if not shotlist_path.exists():
                shotlist_path.write_text("version: 1\nscenes: []\n")

    def generate_screenplay(self) -> None:
        """Writes story/03_screenplay.yaml from outline/brief."""
        screenplay_path = self.project.root / "story" / "03_screenplay.yaml"
        outline_path = self.project.root / "story" / "01_outline.yaml"
        brief_path = self.project.root / "story" / "00_brief.md"

        outline = outline_path.read_text() if outline_path.exists() else ""
        brief = brief_path.read_text() if brief_path.exists() else ""

        schema_path = Path(__file__).parent / "schemas" / "screenplay.schema.json"
        schema = json.loads(schema_path.read_text())

        system = "You are a professional screenwriter. Expand the outline into a detailed screenplay format (slugs, description, dialogue)."
        user = f"Brief:\n{brief}\n\nOutline:\n{outline}\n\nWrite the full screenplay in JSON."

        try:
            data = self._call_structured(
                schema=schema,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            screenplay_path.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception:
            if not screenplay_path.exists():
                screenplay_path.write_text("screenplay: []\n")

    def generate_characters(self) -> None:
        """Writes prompts/characters.yaml from brief."""
        out_path = self.project.root / "prompts" / "characters.yaml"
        brief_path = self.project.root / "story" / "00_brief.md"
        brief = brief_path.read_text() if brief_path.exists() else ""

        schema_path = Path(__file__).parent / "schemas" / "characters.schema.json"
        schema = json.loads(schema_path.read_text())

        system = "You are a casting director. Create specific visual descriptions for characters."
        user = f"Brief:\n{brief}\n\nExtract characters and their visual descriptions (key=name, value=description)."

        try:
            data = self._call_structured(
                schema=schema,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            out_path.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception:
            if not out_path.exists():
                out_path.write_text("characters: {}\n")

    def generate_locations(self) -> None:
        """Writes prompts/locations.yaml from brief."""
        out_path = self.project.root / "prompts" / "locations.yaml"
        brief_path = self.project.root / "story" / "00_brief.md"
        brief = brief_path.read_text() if brief_path.exists() else ""

        schema_path = Path(__file__).parent / "schemas" / "locations.schema.json"
        schema = json.loads(schema_path.read_text())

        system = "You are a location scout. Create specific visual descriptions for locations."
        user = f"Brief:\n{brief}\n\nExtract locations and their visual descriptions (key=name, value=description)."

        try:
            data = self._call_structured(
                schema=schema,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            out_path.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception:
            if not out_path.exists():
                out_path.write_text("locations: {}\n")

    def generate_style_bible(self) -> None:
        """Writes prompts/style_bible.yaml from brief/proposal."""
        out_path = self.project.root / "prompts" / "style_bible.yaml"
        brief_path = self.project.root / "story" / "00_brief.md"
        brief = brief_path.read_text() if brief_path.exists() else ""

        schema = {
            "type": "object",
            "properties": {
                "StyleBible": {
                    "type": "object",
                    "properties": {
                        "Format": {
                            "type": "object",
                            "properties": {
                                "AspectRatio": {"type": "string"},
                                "OverallAesthetic": {"type": "string"},
                            },
                        },
                        "CoreLook": {
                            "type": "object",
                            "properties": {
                                "Rendering": {"type": "object"},
                                "CharacterDesign": {"type": "object"},
                            },
                        },
                        "LightingPlan": {"type": "object"},
                        "AudioBible": {"type": "object"},
                    },
                    "required": ["Format", "CoreLook"],
                }
            },
        }

        system = "You are a visual director. Create a comprehensive style guide (Style Bible) for the movie."
        user = f"Brief:\n{brief}\n\nCreate a style bible defining the visual language, rendering style, lighting, and audio mood."

        try:
            data = self._call_structured(
                schema=schema,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            out_path.write_text(yaml.safe_dump(data, sort_keys=False))
        except Exception:
            if not out_path.exists():
                out_path.write_text("StyleBible: {}\n")

    def generate_clip_specs(
        self,
        *,
        overwrite: bool = False,
        act: int | None = None,
        scene: int | None = None,
    ) -> None:
        """
        Generates prompts/clips/*.yaml from story/04_shotlist.yaml.

        Strategy:
        - Call OpenAI once per scene (keeps context bounded).
        - Receive a list of ClipSpec objects via Structured Outputs.
        - Post-process to enforce project defaults and filesystem naming.
        """
        shotlist_path = self.project.root / "story" / "04_shotlist.yaml"
        if not shotlist_path.exists():
            raise FileNotFoundError(
                "Missing story/04_shotlist.yaml. Run 'story shotlist' first."
            )

        shotlist = yaml.safe_load(shotlist_path.read_text()) or {}
        scenes = shotlist.get("scenes") or []
        if not isinstance(scenes, list):
            raise ValueError("shotlist.scenes must be an array")

        # Load schemas
        batch_schema_path = Path(__file__).parent / "schemas" / "clip_batch.schema.json"
        batch_schema = json.loads(batch_schema_path.read_text())

        # Continuity defaults (from project.env, falls back to template defaults)
        self.project.settings()  # ensure env loaded
        style_profile = os.getenv("PROJECT_STYLE_PROFILE", "default")
        loras_profile = os.getenv("PROJECT_LORAS_PROFILE", "core")
        pipeline_key = (
            os.getenv("PROJECT_DEFAULT_PIPELINE")
            or self.project.settings().default_pipeline
        )

        fps = int(os.getenv("PROJECT_FPS", str(self.project.settings().default_fps)))
        width = int(
            os.getenv("PROJECT_WIDTH", str(self.project.settings().default_width))
        )
        height = int(
            os.getenv("PROJECT_HEIGHT", str(self.project.settings().default_height))
        )
        max_seconds = float(self.project.settings().default_max_seconds)

        # Read prompt dictionaries for context
        style_bible = _load_yaml(self.project.root / "prompts" / "style_bible.yaml")
        chars_doc = _load_yaml(self.project.root / "prompts" / "characters.yaml")
        locs_doc = _load_yaml(self.project.root / "prompts" / "locations.yaml")
        loras_doc = _load_yaml(self.project.root / "prompts" / "loras.yaml")

        # Resolve LoRA bundle into clip.loras entries for determinism (optional but recommended)
        bundles = (
            (loras_doc.get("bundles") or {})
            if isinstance(loras_doc.get("bundles"), dict)
            else {}
        )
        bundle_items = bundles.get(loras_profile) or []
        if not isinstance(bundle_items, list):
            bundle_items = []

        # Iterate scenes and generate clips
        clips_dir = self.project.root / "prompts" / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)

        for sc in scenes:
            try:
                a = int(sc.get("act"))
                sidx = int(sc.get("scene"))
            except Exception:
                continue

            if act is not None and a != act:
                continue
            if scene is not None and sidx != scene:
                continue

            scene_obj = sc

            # If all clip files for this scene exist and overwrite is False, skip
            if not overwrite:
                all_exist = True
                for sh in scene_obj.get("shots") or []:
                    cid = sh.get("clip_id")
                    if not cid:
                        continue
                    if not list(clips_dir.glob(f"{cid}__*.yaml")):
                        all_exist = False
                        break
                if all_exist:
                    continue

            system = (
                "You are a VTX-2 video diffusion prompt engineer for a longform feature. "
                "Generate shot-specific clip specs that stay consistent with the project's continuity. "
                "IMPORTANT: Do NOT repeat the global style bible prefix in every clip prompt; "
                "the application prepends it automatically. "
                "Return JSON matching the schema exactly. No extra keys."
            )

            user = f"""Project prompt bible (for context only; do not copy verbatim into each clip prompt):
GLOBAL_PREFIX:
{style_bible.get("global_prefix","")}

PROFILE_PREFIX[{style_profile}]:
{(style_bible.get("profiles",{}) or {}).get(style_profile,{}).get("prefix","")}

Characters dictionary (keys -> descriptions):
{json.dumps(chars_doc.get("characters", {}), indent=2)}

Locations dictionary (keys -> descriptions):
{json.dumps(locs_doc.get("locations", {}), indent=2)}

Scene:
{json.dumps(scene_obj, indent=2)}

Clip spec requirements:
- One clip spec per shot in scene.shots.
- clip_id must match the shot's clip_id exactly.
- continuity.shared_prompt_profile = "{style_profile}"
- continuity.shared_loras_profile = "{loras_profile}"
- continuity.characters and continuity.locations must use the keys from the shot.
- prompt.positive must be shot-specific: camera framing/motion, subject actions, key props, lighting differences, emotion.
- Keep prompts concise but vivid; avoid contradictions.
- duration: if shot.duration_hint_seconds > 0, set render.duration.mode=fixed and duration.seconds=that value.
  Otherwise use render.duration.mode=auto with min_seconds>=2 and max_seconds<= {max_seconds}.
- Render defaults (you may set these, but the app will enforce):
  pipeline="{pipeline_key}", fps={fps}, width={width}, height={height}, max clip length <=15 seconds.
"""

            try:
                batch = self._call_structured(
                    schema=batch_schema,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
            except Exception:
                # If the API isn't available, create minimal stubs for this scene
                batch = {"version": 1, "clips": []}

            clips = batch.get("clips") or []
            if not isinstance(clips, list):
                clips = []

            # Post-process + write
            shot_map = {
                (sh.get("clip_id") or ""): sh
                for sh in scene_obj.get("shots") or []
                if isinstance(sh, dict)
            }

            for clip in clips:
                if not isinstance(clip, dict):
                    continue
                cid = clip.get("clip_id")
                if not cid or cid not in shot_map:
                    continue

                sh = shot_map[cid]

                # Enforce required structure / defaults
                clip["version"] = 1
                clip.setdefault("title", sh.get("title") or cid)
                clip.setdefault("act", a)
                clip.setdefault("scene", sidx)
                clip.setdefault("shot", int(sh.get("shot", 1)))

                continuity = clip.setdefault("continuity", {})
                continuity["shared_prompt_profile"] = style_profile
                continuity["shared_loras_profile"] = loras_profile
                continuity.setdefault("characters", sh.get("characters") or [])
                continuity.setdefault("locations", sh.get("locations") or [])

                clip.setdefault(
                    "story_beats",
                    sh.get("action_beats") or scene_obj.get("beats") or [],
                )

                prompt = clip.setdefault("prompt", {})
                prompt.setdefault("positive", sh.get("description") or "")
                prompt.setdefault("negative", "")

                render = clip.setdefault("render", {})
                render.setdefault("pipeline", pipeline_key)
                render.setdefault("fps", fps)
                render.setdefault("width", width)
                render.setdefault("height", height)
                render.setdefault("seed", 0)

                # Duration policy
                render.setdefault("duration", {})
                dur = render["duration"] or {}
                if not isinstance(dur, dict):
                    dur = {}
                hint = float(sh.get("duration_hint_seconds") or 0)
                if hint > 0:
                    dur["mode"] = "fixed"
                    dur["seconds"] = min(hint, max_seconds)
                    dur["max_seconds"] = max_seconds
                    dur.setdefault("min_seconds", 0)
                else:
                    dur.setdefault("mode", "auto")
                    dur.setdefault("min_seconds", 2)
                    dur.setdefault("max_seconds", max_seconds)
                render["duration"] = dur

                inputs = clip.setdefault("inputs", {})
                inputs.setdefault("type", "t2v")
                inputs.setdefault("reference_image", None)
                inputs.setdefault("input_video", None)
                inputs.setdefault("keyframes", [])

                # Optional: embed resolved lora bundle for determinism
                if bundle_items and "loras" not in clip:
                    loras_list = []
                    for item in bundle_items:
                        if not isinstance(item, dict):
                            continue
                        env_name = item.get("env")
                        weight = item.get("weight", 0.8)
                        if env_name:
                            loras_list.append(
                                {"env": env_name, "weight": float(weight)}
                            )
                    if loras_list:
                        clip["loras"] = loras_list

                outputs = clip.setdefault("outputs", {})
                fname = f"{cid}__{_slugify(clip.get('title',''))}"
                outputs.setdefault("mp4", f"renders/clips/{fname}.mp4")
                outputs.setdefault("json", f"renders/clips/{fname}.render.json")

                status = clip.setdefault("status", {})
                status.setdefault("state", "planned")
                status.setdefault("last_error", None)

                # Write file
                out_file = clips_dir / f"{fname}.yaml"
                if out_file.exists() and not overwrite:
                    continue
                out_file.write_text(yaml.safe_dump(clip, sort_keys=False))

        # If nothing was generated, ensure the folder exists
        clips_dir.mkdir(parents=True, exist_ok=True)
