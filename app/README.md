# VTX App (LTX-2 / VTX-2 Longform Orchestrator)

This package lives in `LTX-2/app` and provides a Python 3.12 CLI that helps you
produce longform projects as a sequence of short clips rendered with LTX-2 pipelines
(e.g. `ltx_pipelines.ti2vid_two_stages`).

## Features

- **Project Scaffolding**: Consistent folder layout (`projects/<slug>`) with templates.
- **AI-Assisted Pre-Production**:
  - `propose`: Turn a raw idea into a production plan with CivitAI resource suggestions.
  - `story`: Generate outlines, treatments, screenplays, characters, locations, and shotlists using OpenAI.
- **Context Awareness**: CLI commands automatically detect the active project when run from project directories.
- **Rendering Orchestration**: Manage render jobs (drafts vs. production), resuming, and assembly.

## System Assumptions

The LTX-2 toolchain is tested with Python 3.12+ and CUDA 12.x on Linux.

## Installation

1. **Install the app**
   From the `app/` directory:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Configure shared environment**
   ```bash
   cp config/global.env.example config/global.env
   cp config/models.env.example config/models.env
   ```
   *Edit `config/models.env` to point to your local model weights.*

3. **Set API Keys (Optional)**
   If using AI features:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

## Workflow: Automated "create-movie"

To generate a complete project from idea to clip specs in one shot:

```bash
vtx create-movie <slug> "<prompt>"
```

Example:
```bash
vtx create-movie theo_dragon "A young boy named Theo battles an evil dragon in suburbia..."
```

*This runs `propose`, `create-from-plan`, `outline`, `treatment`, `shotlist`, and `clips` automatically.*

## Workflow: The "Vision" Path (Step-by-Step)

This workflow takes a raw concept to a production-ready project with rich style definitions and resource allocations, allowing for manual edits between steps.

### 1. Ideation & Planning
Generate a project proposal from a text file or string.
```bash
# Finds visual style keywords and suggests CivitAI LoRAs
vtx projects propose "A cyberpunk noir set in 2099 rain..."
# OR
vtx projects propose my_idea.txt
```
*Output: `[slug]_plan.yaml`*

### 2. Project Creation
Create the project structure from the generated plan.
```bash
vtx projects create-from-plan [slug]_plan.yaml
```
*Creates `projects/[slug]`, hydrates `story/00_brief.md`, generates `prompts/style_bible.yaml`, and moves the plan file into the project root.*

### 3. Story Development
Navigate to the project directory. The CLI will automatically infer the project context.
```bash
cd projects/[slug]
```

Run the story generators in order:
```bash
# 1. Structure the story (Acts/Scenes)
vtx story outline

# 2. Generate prose description
vtx story treatment

# 3. Generate dialogue and action
vtx story screenplay

# 4. Define Characters and Locations (Visual Prompts)
vtx story characters
vtx story locations

# 5. Break down into shots
vtx story shotlist

# 6. Generate renderable clip specifications
vtx story clips
```

### 4. Production (Rendering)
Render clips directly.
```bash
# View status of all clips
vtx render status [slug]

# Render a specific clip (Draft quality)
vtx render clip [slug] [CLIP_ID] --preset draft

# Approve a clip for V2V refinement
vtx render approve [slug] [CLIP_ID] --strategy v2v

# Render final quality
vtx render clip [slug] [CLIP_ID] --preset final

# Assemble final cut
vtx render assemble [slug]
```

## Manual Workflow

If you prefer to skip the AI planning:

1. **Create Project**: `vtx projects new [slug] --title "My Title"`
2. **Setup Env**: `vtx project env-create [slug]`
3. **Manually Edit**: breakdown your story in `story/` and `prompts/`.
4. **Render**: Use `vtx render` commands as above.

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

## Core Concepts

### Environment Layering
1. OS environment variables
2. `config/global.env`
3. `config/models.env`
4. `projects/<slug>/project.env` (overrides global defaults)

### Clip Specs
Per-clip specs live in `projects/<slug>/prompts/clips/`. They contain prompt text, render configuration, and output paths. The renderer reads these files and updates the shared registry.

### Directory Structure
- `src/vtx_app/cli.py` – CLI entrypoint & command logic.
- `src/vtx_app/story/` – OpenAI integration, prompt builders, schemas.
- `src/vtx_app/render/` – Render planning & orchestration.
- `_global/registry.sqlite` – Multi-project progress registry.
