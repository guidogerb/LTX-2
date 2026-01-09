# Tasks

This file is a production checklist + dev TODO list.

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
- [ ] Write or generate screenplay files:
  - `story/03_screenplay/A01_S01__opening.md`, etc.
- [ ] Generate `story/04_shotlist.yaml`
- [ ] Generate per-clip specs: `prompts/clips/*.yaml`
- [ ] Render previews (lower-res profile)
- [ ] Review + notes in `review/notes/`
- [ ] Update clip specs (prompt tweaks, seed locks, inputs)
- [ ] Render finals (higher-res profile)
- [ ] Assemble:
  - [ ] acts (if enabled)
  - [ ] final cut

## App development TODO

- [ ] Add richer duration estimator (beats -> seconds)
- [ ] Add keyframe interpolation plan mode
- [ ] Add v2v + ic-lora input wiring
- [ ] Add richer registry queries (filters, priorities)
- [ ] Add ffmpeg-based assembler presets (acts/final)
- [ ] Add prompt QA checks (token length, banned phrases, text legibility hints)
