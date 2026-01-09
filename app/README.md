# VTX App (LTX-2 / VTX-2 Longform Orchestrator)

This folder is intended to live at: `LTX-2/packages/app`

It provides a Python 3.12 CLI application that helps you produce **feature-length scripted movies** as a sequence of short clips rendered with LTX-2 pipelines (e.g. `ltx_pipelines.ti2vid_two_stages`), with:
- a **consistent project layout** across many movies
- **shared continuity** (style bible + shared LoRA bundles) across an entire film
- per-project environments (each project owns its own `requirements.txt`)
- a global registry so you can **resume unfinished work** across multiple projects
- optional OpenAI integration to generate outlines, shotlists, and per-clip prompt specs in a fixed schema

## System assumptions

LTX-2 documentation states the codebase was tested with Python >= 3.12 and CUDA > 12.7 (and PyTorch ~= 2.7). Align your environment accordingly. See official docs:
- https://docs.ltx.video/open-source-model/integration-tools/pytorch-api

## Quick start

### 1) App install (this package)

From `LTX-2/packages/app`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Configure shared environment files

Copy examples and edit:

```bash
cp config/global.env.example config/global.env
cp config/models.env.example config/models.env
```

> `config/models.env` is shared across all projects: **put model paths here**.

If you use OpenAI-assisted story generation, also export:

```bash
export OPENAI_API_KEY="..."
```

OpenAI SDKs are designed to read the key from `OPENAI_API_KEY`. See OpenAI docs:
- https://platform.openai.com/docs/libraries

### 3) Create a project

```bash
python -m vtx_app.cli projects new my_movie --title "My Movie"
```

This creates: `projects/my_movie/` (copied from `_global/templates/project_template`)

### 4) Create the project environment

Each movie project owns its own environment file(s):

```bash
python -m vtx_app.cli project env-create my_movie
```

This uses `projects/my_movie/env/requirements.txt`.

### 5) Generate story artifacts (optional)

```bash
python -m vtx_app.cli story outline my_movie
python -m vtx_app.cli story shotlist my_movie
python -m vtx_app.cli story clips my_movie
# (optional filters)
python -m vtx_app.cli story clips my_movie --act 1
python -m vtx_app.cli story clips my_movie --act 1 --scene 2
python -m vtx_app.cli story clips my_movie --overwrite
```

### 6) Render clips / resume unfinished

```bash
python -m vtx_app.cli render clip my_movie A01_S01_SH001
python -m vtx_app.cli render resume --max-jobs 1
```

## Core concepts

### Environment layering

1. OS environment variables
2. `config/global.env`
3. `config/models.env`
4. `projects/<slug>/project.env` (overrides global defaults)

### Acts mode

Set `VTX_PRODUCE_IN_ACTS=true` (global) or `PROJECT_PRODUCE_IN_ACTS=true` (per project)
to assemble outputs by acts (like a musical play).

### Clip length and frames

Projects default to 16 fps and max 15 seconds per clip. The app estimates clip duration from story beats + prompt content (and clamps to max_seconds), then converts to frames. LTX docs mention a max of 257 frames
and recommend 121–161 frames for balanced quality/memory; keep project defaults compatible
with those constraints. See:
- https://docs.ltx.video/open-source-model/usage-guides/text-to-video

## Where to look

- `src/vtx_app/cli.py` – CLI entrypoint
- `src/vtx_app/story/` – schemas, prompt compilation, OpenAI builders
- `src/vtx_app/render/` – render planning & orchestration
- `_global/registry.sqlite` – multi-project progress registry
- `_global/templates/project_template/` – new project template



You picked **B** (outline → shotlist → per‑clip spec generation). I updated the scaffold accordingly and added the missing “clip specs” generator + render-time frame planning.

[Download the updated scaffold (B)](sandbox:/mnt/data/vtx_app_skeleton_B.zip)

## What “B” does now

### 1) OpenAI generates structured story assets

The app uses the **Responses API** for text generation (via the official OpenAI SDK)  and uses **Structured Outputs** so the result must conform to your JSON Schemas .

Pipeline:

1. `story/00_brief.md` → generate `story/01_outline.yaml`
2. outline (+ optional `story/02_treatment.md`) → generate `story/04_shotlist.yaml`
3. shotlist → generate per‑shot `prompts/clips/*.yaml` clip specs (one clip per shot)

### 2) Clip specs are continuity-first

Each generated clip spec references:

* `continuity.shared_prompt_profile` → style profile from `prompts/style_bible.yaml`
* `continuity.characters` → keys from `prompts/characters.yaml`
* `continuity.locations` → keys from `prompts/locations.yaml`
* optional `loras` list → bundle resolved from `prompts/loras.yaml`

At render time, the **prompt compiler** automatically prepends the global/profile style bible and inserts the locked character/location descriptions, so the **clip prompt stays shot-specific**.

### 3) “As short as possible” clips + frames from content

Clip specs store duration policy in `render.duration`:

* `mode: auto` with `min_seconds`/`max_seconds` (default max is 15)
* OR `mode: fixed` with `duration.seconds` (used when a shot needs extra time, e.g., readable text)

Renderer then:

* estimates seconds from story beats + keywords (content-driven)
* converts to frames using FPS
* clamps to `LTX_MAX_FRAMES` (default 257)
* **optionally** passes `--num-frames/--fps/--width/--height/--seed/--negative-prompt` *only if the pipeline’s `--help` shows those flags* (auto-detected)

## New/updated commands

```bash
# Outline
python -m vtx_app.cli story outline my_movie

# Shotlist
python -m vtx_app.cli story shotlist my_movie

# Clip specs (per-shot YAML files)
python -m vtx_app.cli story clips my_movie
python -m vtx_app.cli story clips my_movie --act 1
python -m vtx_app.cli story clips my_movie --act 1 --scene 2
python -m vtx_app.cli story clips my_movie --overwrite
```

Rendering:

```bash
python -m vtx_app.cli render clip my_movie A01_S01_SH001
python -m vtx_app.cli render resume --max-jobs 1
```

## Environment variables (important for OpenAI + consistency)

The OpenAI SDK expects your API key in the environment (not committed into files) .

Add to your shell:

```bash
export OPENAI_API_KEY="..."
```

Global defaults in `config/global.env`:

```dotenv
VTX_OPENAI_MODEL=gpt-4o-2024-08-06
VTX_OPENAI_MAX_OUTPUT_TOKENS=4096
VTX_OPENAI_TEMPERATURE=0.4
```

Notes:

* Structured Outputs (JSON schema) is supported on “latest” models starting with GPT‑4o-era snapshots; if you pick a model that doesn’t support it, you may need to switch models .
* This app uses the **Responses API** and reads the structured result via `response.output_text` .

## Fixed formats (shared across all movie projects)

These are the project-to-project stable artifacts your orchestrator can rely on:

### `story/01_outline.yaml`

Acts → scenes → beats (minimal but consistent).

### `story/04_shotlist.yaml`

Scenes include: `location_key`, `time_of_day`, `beats`, and `shots[]`.

Each shot includes:

* `clip_id` like `A01_S01_SH001`
* `shot_type`, `camera_motion`, `description`, `action_beats`
* `characters[]`, `locations[]` (keys from dictionaries)
* `duration_hint_seconds` (0 = auto)

### `prompts/clips/<clip_id>__<slug>.yaml`

A full renderable “clip spec” including:

* `continuity`
* `story_beats`
* `prompt.positive / prompt.negative`
* `render` (pipeline/fps/resolution/seed/duration)
* `inputs` (t2v/v2v/keyframes future-proofed)
* `outputs.mp4/json`
* `status.state`

## What changed in the scaffold (so you can extend it)

Key additions/improvements:

* `StoryBuilder.generate_shotlist()` implemented (Structured Outputs)
* `StoryBuilder.generate_clip_specs()` implemented (per-scene Structured Outputs → many per-shot YAML files)
* `pipelines/capabilities.py` auto-detects CLI flags via `python -m <module> --help` (so you don’t hardcode every LTX option)
* `story/duration_estimator.py` content-driven seconds → frames
* `prompt_compiler.py` now injects locked character/location descriptions automatically
* `ProjectLoader.sync_all_projects()` now also scans `prompts/clips/*.yaml` and inserts “planned” clips into the registry, so `render resume` actually works across projects

If you want the **next increment** after B, the natural “C” is: generate `story/03_screenplay/` per-scene pages (dialogue + blocking) and then let the shotlist + clip generator draw from that, but B is already enough to produce consistent, render-ready 15s clip specs.
