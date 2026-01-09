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

Projects default to 16 fps and max 15 seconds per clip. LTX docs mention a max of 257 frames
and recommend 121–161 frames for balanced quality/memory; keep project defaults compatible
with those constraints. See:
- https://docs.ltx.video/open-source-model/usage-guides/text-to-video

## Where to look

- `src/vtx_app/cli.py` – CLI entrypoint
- `src/vtx_app/story/` – schemas, prompt compilation, OpenAI builders
- `src/vtx_app/render/` – render planning & orchestration
- `_global/registry.sqlite` – multi-project progress registry
- `_global/templates/project_template/` – new project template
