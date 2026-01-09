# Tasks

This file tracks production steps and a lightweight development backlog for the VTX app.

## Movie production workflow (per project)

- [ ] Create project from template
- [ ] Fill in `metadata.yaml` (title, logline, aspect ratio, fps, pipeline defaults)
- [ ] Lock continuity:
  - [ ] `prompts/style_bible.yaml`
  - [ ] `prompts/characters.yaml`
  - [ ] `prompts/locations.yaml`
  - [ ] `prompts/loras.yaml` (shared LoRA bundles)
- [ ] Write `story/00_brief.md`
- [ ] Generate `story/01_outline.yaml` (acts/scenes/beats)
- [ ] Write or update `story/03_screenplay.yaml` (optional)
- [ ] Generate `story/04_shotlist.yaml`
- [ ] Generate per-clip specs in `prompts/clips/*.yaml` (`<clip_id>__<slug>.yaml`)
- [ ] Render previews (lower-res profile)
- [ ] Review + notes in `review/notes/`
- [ ] Update clip specs (prompt tweaks, seed locks, inputs)
- [ ] Render finals (higher-res profile)

## App development backlog

- [ ] Expose `StoryBuilder.generate_clip_specs` options in the CLI (`--act`, `--scene`, `--overwrite`).
- [ ] Implement ffmpeg helpers and assembly commands (`render/ffmpeg.py`, `render/assembler.py`).
- [ ] Support input modalities in rendering (`inputs.type` for image/video/keyframes).
- [ ] Add schema validation for story/clip YAML files before rendering.
- [ ] Add test coverage for registry syncing, CLI commands, and render argument building.
