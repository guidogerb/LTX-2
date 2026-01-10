# VTX App (LTX-2 / VTX-2 Longform Orchestrator)

This package lives in `LTX-2/app` and provides a Python 3.12 CLI that helps you
produce longform projects as a sequence of short clips rendered with LTX-2 pipelines
(e.g. `ltx_pipelines.ti2vid_two_stages`).

## Features

- Project scaffolding with a consistent folder layout
- Continuity-aware prompt generation (style bible, characters, locations, LoRA bundles)
- Optional OpenAI integration to generate outlines, shotlists, and per-clip specs
- Rendering orchestration with a shared registry for resuming unfinished clips

## System assumptions

The LTX-2 toolchain is tested with Python 3.12 and CUDA 12.x. Align your environment
accordingly.

## Quick start

### 1) Install the app

From `LTX-2/app`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Configure shared environment files

```bash
cp config/global.env.example config/global.env
cp config/models.env.example config/models.env
```

`config/models.env` is shared across all projects. Put model paths there.

If you use OpenAI-assisted story generation:

```bash
export OPENAI_API_KEY="..."
```

### 3) Create a project

```bash
vtx projects new my_movie --title "My Movie"
```

This creates `projects/my_movie/` from `_global/templates/project_template`.

### 4) Create the per-project environment

```bash
vtx project env-create my_movie
```

This installs dependencies from `projects/my_movie/env/requirements.txt`.

### 5) Generate story artifacts (optional)

```bash
vtx story outline my_movie
vtx story shotlist my_movie
vtx story clips my_movie
```

### 6) Render clips / resume unfinished

```bash
vtx render clip my_movie A01_S01_SH001
vtx render resume --max-jobs 1
```

## Proposal & Review Workflow

For a guided setup with drafts and V2V refinement, follow this workflow:

1. **Propose a concept:**
   ```bash
   vtx projects propose "A cyberpunk noir set in 2099 rain..."
   # or
   vtx projects propose my_idea.txt
   ```
   This generates `proposal.yaml` with an AI-analyzed plan and CivitAI resource suggestions.

2. **Create project from plan:**
   Edit the proposal if needed, then run:
   ```bash
   vtx projects create-from-plan proposal.yaml
   ```

3. **Render Drafts (Half-Resolution):**
   Render quick previews at 50% resolution to check composition and timing.
   ```bash
   # Render specific clip
   vtx render clip my_movie A01_S01_SH001 --preset draft
## The Vision Workflow

This workflow (aka "The Vision Workflow") is designed to take a raw concept description and turn it into a production-ready project with rich style definitions, resource allocations (LoRAs), and a full production plan.

### 1) Propose & Plan

Input: A detailed text description of your movie (story, style, vibe).

```bash
vtx projects propose "my_concept.txt" --out proposal.yaml
```

- Analyzes the concept for visual style keywords.
- Searches CivitAI for relevant LoRAs.
- Creates a `proposal.yaml` blueprint.

### 2) Create & Hydrate

```bash
vtx projects create-from-plan proposal.yaml
```

- Creates the project structure.
- Writes `story/00_brief.md`.
- **Generates `prompts/style_bible.yaml`** (Visual language, lighting, audio).
- **Populates `prompts/loras.yaml`** with the suggested LoRAs.

### 3) Story & Specification

```bash
cd projects/<slug>
vtx story outline      # Structure the story (Acts/Scenes)
vtx story treatment    # Prose description
vtx story screenplay   # Dialogue and action
vtx story shotlist     # Shot-by-shot breakdown
vtx story clips        # Generate renderable clip specs
```

### 4) Render Cycle (Draft -> Final)

```bash
# Render 50% res draft
vtx render clip <slug> <clip_id> --preset draft

# Approve and choose strategy (t2v or v2v)
vtx render approve <slug> <clip_id> --strategy v2v

# Render final (v2v uses draft as input)
vtx render clip <slug> <clip_id> --preset final
```

## Development

This project uses `make` to manage development tasks.

```bash
# Format code (Black, isort)
make format

# Run tests
make test

# Verify all (Format + Test)
make verify
```

## Core concepts

### Environment layering

1. OS environment variables
2. `config/global.env`
3. `config/models.env`
4. `projects/<slug>/project.env` (overrides global defaults)

### Clip specs

Per-clip specs live in `projects/<slug>/prompts/clips/` and are stored as
`<clip_id>__<slug>.yaml`. They contain prompt text, render configuration, and output
paths. The renderer reads these files and updates the shared registry.

### Where to look

- `src/vtx_app/cli.py` – CLI entrypoint
- `src/vtx_app/story/` – schemas, prompt compilation, OpenAI builders
- `src/vtx_app/render/` – render planning & orchestration
- `_global/registry.sqlite` – multi-project progress registry
- `_global/templates/project_template/` – new project template

## Current limitations

- Story CLI commands do not yet expose filtering or overwrite options.
