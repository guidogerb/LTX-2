No questions needed — you’ve given enough constraints to design a solid, repeatable layout. Below is a **Python 3.12** application design that lives at **`LTX-2/packages/app`** and supports **VTX scripted, long-form feature production** across multiple projects, with **consistent prompt language + shared LoRAs**, **per-project environments**, and **OpenAI-assisted story/prompt generation**.

(Notes on OpenAI integration: the official SDK reads `OPENAI_API_KEY` from the environment and modern examples use the **Responses API** via `client.responses.create(...)`. ([OpenAI Platform][1]) Structured outputs can enforce JSON schema for consistent story/prompt files. ([OpenAI Platform][2]))

---

## 1) High-level architecture

**Separation of concerns**

* **App code**: lives under `packages/app/src/vtx_app/`
* **Shared configuration** (global + model paths): lives under `packages/app/config/`
* **Projects (movies)**: live under `packages/app/project/` (or elsewhere via env var)
* **Global registry/state**: lives under `packages/app/_global/` (or elsewhere via env var)

**Pipeline abstraction**

* The app wraps these pipeline entrypoints as “render backends”:

  * `ltx_pipelines.ti2vid_two_stages` (recommended)
  * `ltx_pipelines.ti2vid_one_stage`
  * `ltx_pipelines.distilled`
  * `ltx_pipelines.ic_lora`
  * `ltx_pipelines.keyframe_interpolation`

**Core workflow**

1. Create/choose a project
2. Generate outline → screenplay → shotlist → clip specs (optionally with OpenAI)
3. Compile prompts with shared “style bible” + shared LoRAs
4. Render clips (≤15s each; default “as short as possible while covering content well”)
5. Assemble clips into scenes/acts/final cut
6. Resume unfinished work across multiple projects via a global registry

---

## 2) Proposed folder layout (rooted at `LTX-2/packages/app`)

```text
LTX-2/
  packages/
    app/
      README.md
      tasks.md
      pyproject.toml

      config/
        global.env.example
        models.env.example
        logging.yaml

      _global/
        registry.sqlite
        projects_index.json
        templates/
          project_template/
            metadata.yaml
            project.env.example
            env/
              requirements.txt
            story/
              00_brief.md
              01_outline.yaml
              02_treatment.md
              03_screenplay/
              04_shotlist.yaml
            prompts/
              style_bible.yaml
              characters.yaml
              locations.yaml
              loras.yaml
              clips/
            inputs/
              reference_images/
              keyframes/
              video_sources/
              audio/
            renders/
              clips/
              acts/
              final/
            review/
              notes/
            logs/

      project/
        <project_slug>/
          metadata.yaml
          project.env
          env/
            requirements.txt
            constraints.txt
            python_version.txt
          story/
            00_brief.md
            01_outline.yaml
            02_treatment.md
            03_screenplay/
              A01_S01__opening.md
              A01_S02__...md
            04_shotlist.yaml
          prompts/
            style_bible.yaml
            characters.yaml
            locations.yaml
            loras.yaml
            clips/
              A01_S01_SH001__dawn_establishing.yaml
              A01_S01_SH002__hero_closeup.yaml
              ...
          inputs/
            reference_images/
            keyframes/
            video_sources/
            audio/
          renders/
            clips/
            acts/
            final/
          review/
            notes/
            selects/
          logs/

      src/
        vtx_app/
          __init__.py
          cli.py

          config/
            __init__.py
            env_layers.py
            settings.py
            paths.py

          registry/
            __init__.py
            db.py
            models.py
            sync.py
            status.py

          project/
            __init__.py
            loader.py
            layout.py
            validation.py

          story/
            __init__.py
            formats.py
            schemas/
              story.schema.json
              shotlist.schema.json
              clip.schema.json
            openai_builder.py
            prompt_compiler.py
            duration_estimator.py

          pipelines/
            __init__.py
            base.py
            runner_subprocess.py
            ti2vid_two_stages.py
            ti2vid_one_stage.py
            distilled.py
            ic_lora.py
            keyframe_interpolation.py

          render/
            __init__.py
            planner.py
            renderer.py
            assembler.py
            ffmpeg.py
            cache.py

          utils/
            __init__.py
            hashing.py
            logging.py
            timecode.py
```

### Why this works

* **Consistent project layout** makes multi-project tooling trivial (scan + resume + batch).
* **`config/models.env`** is shared across all projects; **`project.env`** overrides per project.
* Templates guarantee every project uses the same fixed formats.

---

## 3) Environment variables and layering rules

### 3.1 Shared model env vars (ONE file for all projects)

File: `packages/app/config/models.env` (not committed; commit `models.env.example`)

Recommended keys (map 1:1 to pipeline args):

```bash
# Core models
LTX_CHECKPOINT_PATH=/models/vtx2/checkpoint.safetensors
LTX_DISTILLED_LORA_PATH=/models/vtx2/distilled_lora.safetensors
LTX_SPATIAL_UPSAMPLER_PATH=/models/vtx2/upsampler.safetensors
LTX_GEMMA_ROOT=/models/gemma

# Optional / pipeline-specific
LTX_IC_LORA_PATH=/models/vtx2/ic_lora.safetensors

# Default render targets (4090-friendly)
LTX_DEFAULT_WIDTH=1536
LTX_DEFAULT_HEIGHT=864
LTX_DEFAULT_FPS=16
LTX_DEFAULT_ASPECT=16:9
LTX_DEFAULT_MAX_SECONDS=15
```

### 3.2 Global app env vars (shared across all projects)

File: `packages/app/config/global.env` (not committed; commit `global.env.example`)

```bash
# Where global registry + caches live
VTX_APP_HOME=packages/app/_global

# Where projects live (can be external)
VTX_PROJECTS_ROOT=packages/app/projects

# Produce outputs grouped by acts (musical-play mode)
VTX_PRODUCE_IN_ACTS=true

# Defaults
VTX_DEFAULT_PIPELINE=ti2vid_two_stages
VTX_FAIL_FAST=false
VTX_MAX_PARALLEL_JOBS=1
```

### 3.3 Project-specific env vars (inside each project)

File: `project/<slug>/project.env`

```bash
PROJECT_TITLE="My Feature Film"
PROJECT_ASPECT=2.39:1
PROJECT_WIDTH=1920
PROJECT_HEIGHT=800
PROJECT_FPS=16

# Override style bible or shared loras if needed
PROJECT_STYLE_PROFILE=default

# Acts override (project can force acts even if global off)
PROJECT_PRODUCE_IN_ACTS=true
```

### 3.4 OpenAI env vars (global; never stored in projects)

* `OPENAI_API_KEY` (recommended) ([OpenAI Platform][1])
  Optionally:
* `OPENAI_BASE_URL` (if using a proxy)
* `OPENAI_PROJECT` / `OPENAI_ORG` (if your org config requires it)

OpenAI calls will use the official SDK and **Responses API**. ([OpenAI Platform][3])

---

## 4) Per-project environment creation (as you requested)

Each project has its own env spec at:
`project/<slug>/env/requirements.txt` (+ optional `constraints.txt`)

Example `requirements.txt`:

```text
openai>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
typer>=0.12.0
rich>=13.0.0
PyYAML>=6.0.0
```

The app can provide a command:

```bash
python -m vtx_app.cli project env-create <project_slug>
```

which creates:
`project/<slug>/.venv/` and installs from that project’s env files.

This satisfies: **“environment created from a file belonging to a distinct project.”**

---

## 5) Fixed file formats (shared across all movie projects)

To keep your projects compatible, every project produces the same canonical artifacts:

### 5.1 `metadata.yaml` (project identity + production settings)

Location: `project/<slug>/metadata.yaml`

Key fields:

* `project_id` (UUID)
* `title`, `logline`
* `acts_enabled` (defaulted from env but stored here)
* `default_pipeline`, `default_resolution`, `fps`
* `style_profile` pointer
* `created_at`, `updated_at`

### 5.2 Screenplay naming (temporal + descriptive)

`story/03_screenplay/A01_S03__the_library_reveal.md`

Pattern:

* `A{act:02d}_S{scene:02d}__{slug}.md`

### 5.3 Clip spec files (one file per clip)

Location: `prompts/clips/A01_S03_SH005__bro_able_plaque_closeup.yaml`

**Clip spec (proposed v1 schema)**

```yaml
version: 1
clip_id: A01_S03_SH005
title: "Plaque close-up"
act: 1
scene: 3
shot: 5

continuity:
  shared_prompt_profile: "default"
  shared_loras_profile: "core"

story_beats:
  - "Camera settles on the brass plate."
  - "Hold long enough to read the inscription."

prompt:
  positive: |
    (clip-specific text here; no repeated style boilerplate)
  negative: |
    (optional clip-specific negatives)

render:
  pipeline: "ti2vid_two_stages"
  duration:
    mode: "auto"          # auto | fixed
    max_seconds: 15
    min_seconds: 2
  fps: 16
  width: 1920
  height: 800
  seed: 123456
  guidance_scale: 4.0
  notes: "As short as possible while covering content well."

inputs:
  type: "t2v"             # t2v | i2v | v2v | keyframe_interpolation
  reference_image: null
  input_video: null
  keyframes: []

loras:
  - env_path: "LTX_DISTILLED_LORA_PATH"
    weight: 0.8

outputs:
  mp4: "renders/clips/A01_S03_SH005__bro_able_plaque_closeup.mp4"
  json: "renders/clips/A01_S03_SH005__...render.json"

status:
  state: "planned"        # planned | queued | rendering | rendered | approved | rejected
  last_error: null
```

### 5.4 Shared “consistency” files

Location: `project/<slug>/prompts/`

* `style_bible.yaml`

  * global prompt prefix (camera/lighting/film stock)
  * global negatives
  * default “shared descriptive language”
* `characters.yaml`

  * canonical descriptors per character
* `locations.yaml`

  * canonical descriptors per location/set
* `loras.yaml`

  * named LoRA bundles (core continuity pack, dream pack, flashback pack)

**Prompt compilation rule**
Final prompt =
`style_bible.global_prefix` + `character/location inserts` + `clip.positive`

This prevents drift and keeps the “same movie” feel.

---

## 6) Pipeline runner design (maps clip specs → `python -m ltx_pipelines...`)

### 6.1 “backend” mapping table

* `ti2vid_two_stages` → `python -m ltx_pipelines.ti2vid_two_stages ...`
* `ti2vid_one_stage` → `python -m ltx_pipelines.ti2vid_one_stage ...`
* `distilled` → `python -m ltx_pipelines.distilled ...`
* `ic_lora` → `python -m ltx_pipelines.ic_lora ...`
* `keyframe_interpolation` → `python -m ltx_pipelines.keyframe_interpolation ...`

### 6.2 Example command build (two-stage)

Your app constructs something like:

```bash
python -m ltx_pipelines.ti2vid_two_stages \
  --checkpoint-path "$LTX_CHECKPOINT_PATH" \
  --distilled-lora "$LTX_DISTILLED_LORA_PATH" 0.8 \
  --spatial-upsampler-path "$LTX_SPATIAL_UPSAMPLER_PATH" \
  --gemma-root "$LTX_GEMMA_ROOT" \
  --prompt "<compiled prompt>" \
  --output-path "<project>/renders/clips/<clip>.mp4"
```

### 6.3 Duration → frames rule

* If `duration.mode == auto`:

  * estimate seconds from `story_beats` (+ optional LLM duration estimate)
  * clamp to `[min_seconds, max_seconds]`
* frames = `round(fps * seconds)`

This satisfies: “number of frames determined by the content of the prompts” (beats/LLM-derived timing), not a fixed default.

---

## 7) OpenAI story/prompt generation (fixed format, multi-project compatible)

### 7.1 Why structured outputs

To guarantee every project produces the same schema-shaped files, use **Structured Outputs** with JSON schema. ([OpenAI Platform][2])

### 7.2 API usage

Use the official SDK (`OpenAI()`) and `client.responses.create(...)`. ([OpenAI Platform][3])
SDK config expects `OPENAI_API_KEY` via environment variable. ([OpenAI Platform][1])

### 7.3 Builder stages (repeatable per project)

Commands (conceptual):

* `vtx story outline <project>`
* `vtx story screenplay <project>`
* `vtx story shotlist <project>`
* `vtx story clips <project>` (generates `prompts/clips/*.yaml`)

Each stage writes deterministic files into `story/` and `prompts/` using your fixed schemas.

---

## 8) Global registry for “resume unfinished across multiple projects”

Use SQLite at:

* `packages/app/_global/registry.sqlite` (or `VTX_APP_HOME`)

Store:

* projects table: `project_id`, `slug`, `path`, `title`, `active`, `last_opened`
* clips table: `project_id`, `clip_id`, `state`, `hash`, `output_path`, `updated_at`, `error`
* jobs table: queued renders (so you can resume after a crash)

App behavior:

* On startup: scan `VTX_PROJECTS_ROOT`, load `metadata.yaml`, sync registry
* “Work on unfinished” = query registry where `clip.state != rendered/approved`

---

## 9) CLI surface (minimal but powerful)

Proposed commands:

```bash
# List projects + their completion status
vtx projects list
vtx projects status <slug>

# Create a new project from template
vtx projects new <slug> --title "..."

# Create/activate per-project venv
vtx project env-create <slug>

# Generate story artifacts (OpenAI optional)
vtx story outline <slug>
vtx story screenplay <slug>
vtx story shotlist <slug>
vtx story clips <slug>

# Render
vtx render clip <slug> A01_S01_SH001
vtx render scene <slug> A01_S01
vtx render act <slug> A01
vtx render all <slug> --resume

# Assemble
vtx assemble act <slug> A01
vtx assemble final <slug>
```

---

## 10) What goes into `README.md` and `tasks.md`

### `README.md` should include

* What this app is (multi-project VTX-2 longform orchestration)
* Install steps (repo env + project env)
* Env layering rules (global, models, project)
* Project template + fixed formats
* Typical workflow commands
* Troubleshooting (missing model paths, missing `OPENAI_API_KEY`, render caching)

(Include OpenAI setup note: export `OPENAI_API_KEY` and keep it out of repos. ([OpenAI Platform][1]))

### `tasks.md` should include

A production checklist like:

* [ ] Write brief → treatment → outline
* [ ] Lock style bible and LoRA bundle (continuity)
* [ ] Generate screenplay files
* [ ] Generate shotlist
* [ ] Generate clip specs (≤15s each)
* [ ] Render previews (low-res)
* [ ] Review + notes
* [ ] Final renders (higher-res)
* [ ] Assemble acts (if enabled) then assemble final
* [ ] QC pass

---

## 11) RTX 4090 “optimized defaults” (practical)

These live in global env and can be overridden per project/clip:

* Default pipeline: `ti2vid_two_stages`
* Default fps: `16`
* Default max clip length: `15s`
* Default “good quality” resolution:

  * 16:9 → `1536×864`
  * 2.39:1 → `1920×800`
* `VTX_MAX_PARALLEL_JOBS=1` (single GPU queue for stability)

---

If you want one optional enhancement (no questions required): I can also propose **the exact JSON Schemas** for `outline.yaml`, `shotlist.yaml`, and `clip.yaml` so your OpenAI generation is guaranteed to stay compatible across projects using Structured Outputs. ([OpenAI Platform][2])

[1]: https://platform.openai.com/docs/quickstart?utm_source=chatgpt.com "Developer quickstart - OpenAI API"
[2]: https://platform.openai.com/docs/guides/structured-outputs?utm_source=chatgpt.com "Structured model outputs | OpenAI API"
[3]: https://platform.openai.com/docs/overview?lang=python&utm_source=chatgpt.com "Overview | OpenAI Platform"

Continuing with the **concrete spec + fixed schemas + OpenAI builder format + a working skeleton you can drop into `LTX-2/packages/app`**.

## Downloadable starter scaffold

I generated a ready-to-copy folder skeleton (code + docs + template project + schemas):

[Download the skeleton zip](sandbox:/mnt/data/vtx_app_skeleton.zip)

Unzip it into your repo at:

```text
LTX-2/packages/app/
```

It includes:

* `src/vtx_app/` (Typer CLI, registry, prompt compiler, render controller)
* `config/models.env.example` + `config/global.env.example`
* `_global/templates/project_template/` (canonical project layout)
* `story/schemas/*.json` (fixed formats)
* `README.md` + `tasks.md`

---

## Non-negotiable constraints baked into the design

### Python/CUDA compatibility

LTX docs indicate the codebase was tested with **Python >= 3.12** and **CUDA > 12.7**, and PyTorch ~= 2.7.
(Your RTX 4090 is a great fit for this.)

### Frame budget and clip duration

LTX Text-to-Video guidance calls out:

* **Max ~257 frames**
* **Recommended 121–161 frames** for balanced quality/memory
* FPS examples (24/25/30) and the importance of matching FPS across nodes

Your requirement “**clips up to 15 seconds**” is compatible if your default FPS stays reasonable (e.g., **16fps → 240 frames** for 15s, under 257). The app therefore defaults to **16fps**, and clamps to both `max_seconds` and `LTX_MAX_FRAMES`.

### Continuity via shared language + shared LoRA bundles

LTX’s LoRA docs explicitly frame LoRAs as a mechanism to enforce style/subject consistency and even motion/camera behavior.
So the app enforces:

* every clip references a `shared_prompt_profile` (style bible profile)
* every clip references a `shared_loras_profile` (bundle name)
* final prompt is compiled from the same “bible + inserts” system

---

## The “fixed format” contract across all movie projects

This is the most important part for multi-project automation and OpenAI generation.

### 1) Canonical project layout

Every project **must** have these (the template enforces it):

```text
metadata.yaml
project.env
env/requirements.txt

story/
  00_brief.md
  01_outline.yaml
  02_treatment.md
  03_screenplay/
  04_shotlist.yaml

prompts/
  style_bible.yaml
  characters.yaml
  locations.yaml
  loras.yaml
  clips/*.yaml

renders/
  clips/
  acts/
  final/
```

### 2) Temporal + descriptive naming rules

**Screenplay files**

* `A01_S01__opening.md`
* `A02_S03__the_deal_goes_bad.md`

**Clip specs**

* `A01_S01_SH001__dawn_establishing.yaml`
* `A01_S03_SH005__bro_able_plaque_closeup.yaml`

Clip IDs follow:

* `A{act:02d}_S{scene:02d}_SH{shot:03d}`

### 3) Schemas (v1) that OpenAI must output

The skeleton includes:

* `src/vtx_app/story/schemas/story.schema.json`
* `src/vtx_app/story/schemas/shotlist.schema.json`
* `src/vtx_app/story/schemas/clip.schema.json`

The idea is:

* you can validate every YAML as JSON against these schemas
* you can send these schemas directly to OpenAI Structured Outputs so generation cannot drift

OpenAI Structured Outputs is designed to adhere to a provided JSON Schema (unlike older “JSON mode”).

---

## OpenAI integration design (how the app should generate story assets)

### Environment variables

OpenAI’s official docs recommend exporting `OPENAI_API_KEY`, and note the SDK reads it from the environment automatically.

### API usage: Responses API + Structured Outputs

The Responses API is OpenAI’s primary interface for generating text/JSON outputs.
And Structured Outputs can be enabled with a `json_schema` format.

**Recommended approach for your pipeline:**

* Outline generation → enforce `story.schema.json`
* Shotlist generation → enforce `shotlist.schema.json`
* Clip spec generation → enforce `clip.schema.json` per clip (or as a list of clips)

In the skeleton, `StoryBuilder.generate_outline()` demonstrates the core call pattern:

* `client.responses.create(...)`
* `text.format = {"type": "json_schema", "strict": true, ...}`

> If you prefer even tighter typing, OpenAI’s structured outputs guide also shows a `responses.parse(...)` pattern (Pydantic-like parsing).

### Fixed “handoff format” between stages

To keep continuity stable across an entire feature:

1. **Brief (`00_brief.md`)** – human-authored constraints & must-haves
2. **Outline (`01_outline.yaml`)** – acts/scenes/beats
3. **Screenplay (`03_screenplay/*.md`)** – dialogue + performance intent
4. **Shotlist (`04_shotlist.yaml`)** – camera language + story function per shot
5. **Clip specs (`prompts/clips/*.yaml`)** – renderable prompt + settings

Your app should treat **clip specs as the single source of truth** for rendering.

---

## Prompt & LoRA consistency mechanism

### `prompts/style_bible.yaml`

Holds:

* `global_prefix` (the shared descriptive language for the whole film)
* `global_negative`
* `profiles.<name>.prefix/negative` (e.g., “default”, “flashback”, “dream”)

### `prompts/loras.yaml`

Holds named bundles:

* `core` continuity pack (character LoRAs + camera LoRAs + maybe motion LoRAs)
* optional per-act/per-location bundles

LTX’s docs list official camera-motion LoRAs (dolly/jib/static, etc.), which map cleanly into this bundle system.

### Clip spec references (the enforcement point)

Every `prompts/clips/*.yaml` contains:

* `continuity.shared_prompt_profile`
* `continuity.shared_loras_profile`

So the compiler always produces:

```text
FINAL_POSITIVE = global_prefix + profile_prefix + inserts + clip_specific_positive
FINAL_NEGATIVE = global_negative + profile_negative + clip_specific_negative
FINAL_LORAS    = loras.bundle[shared_loras_profile] (+ optional clip overrides)
```

---

## Duration & frame determination (“as short as possible” but content-driven)

### Deterministic default (no LLM needed)

Use `story_beats` count and shot type hints:

Example heuristic:

* establishing shot: 4–7 seconds
* dialogue reaction shot: 2–4 seconds
* action beat: 3–6 seconds
* “readable prop text”: 3–5 seconds (hold time)

Then:

* `seconds = clamp(estimated, min_seconds, max_seconds)`
* `frames = min(round(seconds * fps), LTX_MAX_FRAMES)`

### Optional LLM refinement

A second OpenAI call can output:

* `recommended_seconds`
* `camera_motion_summary`
* `risk_flags` (identity drift, too much text, too many entities, etc.)

But even then: you still clamp to the same constraints.

---

## Global registry behavior (multi-project resume)

The central registry (`_global/registry.sqlite`) tracks:

* projects discovered under `VTX_PROJECTS_ROOT`
* clip render states (`planned/queued/rendering/rendered/approved/rejected`)
* output paths and errors

This enables:

* `vtx render resume` to find unfinished clips across **all projects**
* “pick up where you left off” after crashes or partial renders

---

## Pipeline module support (your list, made operational)

The skeleton maps pipeline keys → module names:

* `ti2vid_two_stages` → `ltx_pipelines.ti2vid_two_stages` (**recommended**)
* `ti2vid_one_stage` → `ltx_pipelines.ti2vid_one_stage`
* `distilled` → `ltx_pipelines.distilled`
* `ic_lora` → `ltx_pipelines.ic_lora`
* `keyframe_interpolation` → `ltx_pipelines.keyframe_interpolation`

The renderer constructs:

```bash
python -m <module> ... --prompt "<compiled>" --output-path "<mp4>"
```

Model locations come from `config/models.env` (shared across all projects), and project overrides live in each `project.env`.

---

## “Acts mode” (musical play style)

Two layers:

* Global: `VTX_PRODUCE_IN_ACTS=true|false`
* Project override: `PROJECT_PRODUCE_IN_ACTS=true|false`

When enabled:

* assembly outputs are grouped under:

  * `renders/acts/A01.mp4`, `renders/acts/A02.mp4`, …
* final cut can be concatenation of act renders into:

  * `renders/final/<project>__final.mp4`

---

## What I would implement next (already aligned to your requirements)

1. **Clip spec generator** (`StoryBuilder.generate_clip_specs`)

* input: `01_outline.yaml`, `04_shotlist.yaml`, `style_bible.yaml`, `loras.yaml`
* output: `prompts/clips/*.yaml` validated against `clip.schema.json`

2. **LoRA bundle resolver**

* convert `shared_loras_profile` → concrete `--distilled-lora path weight` args
* support multiple LoRAs, weights, and pipeline-specific flags

3. **Assembler**

* ffmpeg concat lists per scene/act/final
* respects acts mode automatically

4. **Render caching**

* compute a stable hash from:

  * compiled prompt, negative, lora bundle, pipeline, seed, fps, frames, dims
* skip rendering if identical output already exists

---
