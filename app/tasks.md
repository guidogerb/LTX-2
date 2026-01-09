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

# VTX App — Codex Task Plan (100% coverage)

> **Location in repo:** `LTX-2/packages/app/tasks.md`  
> **Project name:** `vtx-app` (Python 3.12)  
> **Goal:** A robust CLI orchestrator for **Lightricks / VTX-2 (LTX-2 repo)** pipelines that can produce a **feature-length movie** as a collection of **short clips (≤ 15s each)** with **continuity** (shared descriptive language + shared LoRA bundles), and can **resume unfinished work across multiple projects**.

This file is a **complete, explicit task breakdown** meant for **Codex**. It includes:
- the *full specification* (what “done” means)
- the *current scaffold status* (what exists now)
- a step-by-step plan to finish implementation with **100% test coverage**
- quality gates, acceptance criteria, and recommended test strategy

---

## 0) Specification summary (source-of-truth)

### 0.1 Core product requirements
- The application root is **`LTX-2/packages/app`** (this folder).
- Application code must be separate from movie projects.
- Movie projects follow a **fixed folder layout** so the app can work across many projects consistently.
- **Model paths** must be managed via a **single shared env file** used by all projects (`config/models.env`).
- **Global app env vars** must be shared across all projects (`config/global.env`).
- **Project-specific env vars** live inside each project (`<project>/project.env`) and override global defaults.
- Each clip is rendered via an LTX pipeline module:
  - `ltx_pipelines.ti2vid_two_stages` — Two-stage text/image-to-video (recommended).
  - `ltx_pipelines.ti2vid_one_stage` — Single-stage text/image-to-video.
  - `ltx_pipelines.distilled` — Fast text/image-to-video using only the distilled model.
  - `ltx_pipelines.ic_lora` — Video-to-video with IC-LoRA.
  - `ltx_pipelines.keyframe_interpolation` — Keyframe interpolation.
- **Continuity**: prompts must share descriptive language and LoRAs across the movie.
- Clip length:
  - Each clip is **up to 15 seconds**.
  - Default behavior is **“as short as possible while covering the content well.”**
  - Frame count is determined by prompt content (beats / hints), not a single fixed constant.
- “Acts mode”:
  - Support env var for producing the movie in **acts** like a musical play (`VTX_PRODUCE_IN_ACTS`), with a per-project override.
- OpenAI integration:
  - The app can call OpenAI endpoints to generate outline/shotlist/clip specs.
  - Story + prompt artifacts must follow a **fixed format** across all projects (schemas).
- Multi-project work:
  - Project metadata and clip statuses must be tracked in a **central global registry** so the app can pick up unfinished work across multiple projects.

### 0.2 Non-functional requirements
- Must be **fully functional** in a headless environment (no GUI required).
- Must be resilient to partial failure: can resume after crashes.
- Must have **100% automated test coverage** (line coverage; prefer also branch coverage where practical).
- Tests must not require GPU/models/network:
  - Mock subprocess calls (pipeline execution and ffmpeg).
  - Mock OpenAI client calls.
- Provide clear documentation:
  - `README.md` (how to install/use)
  - This `tasks.md` (dev plan)
  - Example configs and template project.

---

## 1) Current status of scaffold (what exists today)

The scaffold currently includes (verify in `packages/app`):
- `pyproject.toml` with runtime deps (`typer`, `rich`, `pydantic`, `python-dotenv`, `PyYAML`, `openai`).
- `config/global.env.example` and `config/models.env.example`.
- `_global/templates/project_template/` with canonical layout and sample metadata.
- `src/vtx_app/` package with:
  - `config/` environment layering and `Settings` parsing (**partially incomplete**)
  - `registry/db.py` SQLite registry implementation (basic)
  - `project/loader.py` + `project/layout.py` (project create/load + per-project venv)
  - `story/openai_builder.py` (outline/shotlist/clip spec generation using OpenAI Responses API + JSON schema)
  - `story/schemas/*.json` fixed schemas for outline/shotlist/clip specs
  - `story/prompt_compiler.py` (continuity injection)
  - `story/duration_estimator.py` (basic content-driven seconds estimator)
  - `pipelines/capabilities.py` (auto-detect supported flags by running `python -m <module> --help`)
  - `pipelines/runner_subprocess.py` (subprocess runner)
  - `render/renderer.py` (**partially incomplete**) render controller and resume logic
  - `render/ffmpeg.py` (**stub**) and `render/assembler.py` (**stub**)

Known incomplete areas:
- `src/vtx_app/cli.py` is incomplete (missing commands wiring).
- `src/vtx_app/config/env_layers.py` is incomplete (missing app-root resolution + file detection).
- `src/vtx_app/render/renderer.py` has an unfinished large portion (render_clip arg building, state updates).
- `render/ffmpeg.py` and `render/assembler.py` are TODO stubs.
- No `tests/` directory yet; no CI; no lint/type configuration.

> **Codex directive:** treat the scaffold as the starting point; do not rewrite architecture unless required. Fill gaps, add tests, and harden behavior.

---

## 2) Definition of Done (DoD) + Quality Gates

### 2.1 “Done” means
- `pip install -e .` works from `packages/app`.
- `vtx --help` works and lists all top-level commands.
- Creating a project from template works:
  - `vtx projects new my_movie --title "..."` creates the full folder structure.
- Project discovery works:
  - `vtx projects list` shows projects from `VTX_PROJECTS_ROOT`.
- OpenAI generation works (when enabled):
  - `vtx story outline <slug>`
  - `vtx story shotlist <slug>`
  - `vtx story clips <slug>` generates per-shot clip spec YAML files.
- Rendering works (with models available):
  - `vtx render clip <slug> A01_S01_SH001`
  - `vtx render resume`
- Registry works:
  - `vtx projects status <slug>` shows counts of planned/rendered/approved.
  - Resume renders clips not yet rendered across many projects.
- Assembler works (ffmpeg installed):
  - `vtx assemble act <slug> A01`
  - `vtx assemble final <slug>`
- Acts mode works:
  - When enabled globally or for a project, outputs are grouped in `renders/acts/`.
- 100% tests:
  - `pytest --cov=vtx_app --cov-report=term-missing --cov-fail-under=100` passes.
  - All subprocess/OpenAI calls are mocked in tests.

### 2.2 Coding standards
- No hidden network calls in non-OpenAI paths.
- All file paths must be `pathlib.Path`.
- YAML writes must be stable (`sort_keys=False`) and avoid lossy conversions.
- Errors must be actionable (include paths and the missing setting name).

---

## 3) Milestone plan (Codex execution order)

> Each milestone should land with tests, docs updates if needed, and no regressions.

---

# Milestone A — Dev tooling + test harness

## A1) Add dev dependencies
- [ ] Add a `[project.optional-dependencies]` section for `dev` in `pyproject.toml` including:
  - `pytest`, `pytest-cov`
  - `ruff`
  - `mypy`
  - `types-PyYAML`
  - `jsonschema` (recommended for schema validation)
- [ ] Add minimal `tool.pytest.ini_options` in `pyproject.toml`:
  - `testpaths = ["tests"]`
  - strict warnings where reasonable
- [ ] Add `tool.coverage.run` and `tool.coverage.report` configuration:
  - `branch = true` if feasible
  - `omit = ["**/__init__.py"]` if necessary to make 100% feasible
  - Use `# pragma: no cover` sparingly for truly unreachable branches.

## A2) Create test skeleton
- [ ] Create `packages/app/tests/` with:
  - `conftest.py` fixtures:
    - temp app root and temp projects root
    - temp `_global` registry path (sqlite file in temp dir)
    - environment variable isolator fixture that clears relevant env vars
- [ ] Add a “smoke” test that imports `vtx_app` and runs `python -m vtx_app.cli --help` (via Typer runner, not subprocess).

## A3) CI-ready commands
- [ ] Add `Makefile` or `scripts/` (optional) for:
  - `make test` → `pytest ...`
  - `make lint` → `ruff check .`
  - `make format` → `ruff format .` (if using ruff formatting)
  - `make type` → `mypy src/vtx_app`

Acceptance criteria:
- [ ] `pytest` passes (even if only a few tests exist).
- [ ] Coverage enforcement is wired but may initially be waived until Milestone D (use `--cov-fail-under=0` temporarily if needed; remove before final).

---

# Milestone B — Finish environment layering + settings

## B1) Complete `config/env_layers.py`
Tasks:
- [ ] Implement app-root discovery robustly:
  - Resolve `packages/app` from `env_layers.py` file location.
  - Do not rely on CWD.
- [ ] Determine the env file locations:
  - `packages/app/config/global.env` and `packages/app/config/models.env`
- [ ] Ensure `load_env(project_env_path=...)` loads in this order:
  1) OS env (already set)
  2) `global.env` (override=False)
  3) `models.env` (override=False)
  4) project env (override=True)
- [ ] Add defensive behavior:
  - If env files don’t exist, do nothing (no exception).
  - Provide `get_bool()` robust parsing (already present).

Tests:
- [ ] Unit test layering precedence with temp files:
  - global defines `X=1`
  - models defines `Y=2`
  - project overrides `X=3`
  - ensure env resolves to X=3, Y=2
- [ ] Test “missing env files” doesn’t crash.

## B2) Harden `Settings.from_env()`
Tasks:
- [ ] Ensure `Settings.from_env()`:
  - Parses required paths as `Path`
  - Normalizes to absolute paths when appropriate
  - Includes OpenAI settings, default render settings, model paths
- [ ] Add validation helpers:
  - `Settings.require_model_paths(pipeline_key)` that raises a clear error if needed env vars missing.

Tests:
- [ ] Verify defaults are applied when env vars absent.
- [ ] Verify required model path validation errors are readable (message contains env var name).

Acceptance criteria:
- [ ] 100% tests for env/settings modules.

---

# Milestone C — Complete CLI surface (Typer)

## C1) Finish `src/vtx_app/cli.py`
Tasks:
- [ ] Wire Typer sub-apps:
  - `projects` group: list/new/status
  - `project` group: env-create
  - `story` group: outline/shotlist/clips
  - `render` group: clip/resume
  - `assemble` group: act/final (later milestone)
- [ ] Ensure all commands:
  - return non-zero exit codes on errors (Typer exceptions)
  - print helpful Rich output
- [ ] Add `--verbose` global option (optional) to increase logging.

Tests:
- [ ] Use `typer.testing.CliRunner` to test each command:
  - `vtx projects list` in empty projects root
  - `vtx projects new ...` creates directories
  - `vtx story outline` calls OpenAI builder (mocked)
  - `vtx render clip` calls render controller (mocked)
- [ ] Snapshot-style tests for `--help` output (keep stable).

Acceptance criteria:
- [ ] CLI is complete and tested.

---

# Milestone D — Project template + registry sync

## D1) Project template creation
Tasks:
- [ ] Confirm `ProjectLoader.create_project()`:
  - Validates slug (safe folder name)
  - Copies `_global/templates/project_template/` into `projects/<slug>`
  - Generates new UUID in `metadata.yaml`
  - Writes title/logline if provided
  - Copies `project.env.example` → `project.env`
- [ ] Ensure idempotency:
  - creating an existing project slug should fail with clear error.

Tests:
- [ ] Create project in temp dir and assert:
  - required folders exist
  - metadata fields set
  - `project.env` exists

## D2) Registry: sync projects + sync clips
Tasks:
- [ ] `ProjectLoader.sync_all_projects()` should:
  - scan `VTX_PROJECTS_ROOT` for `metadata.yaml`
  - upsert into registry
  - discover `prompts/clips/*.yaml` and upsert clip rows with default state
- [ ] Add `Registry` query methods needed by CLI:
  - list projects
  - list clips by project
  - count states
  - update clip state with error info

Tests:
- [ ] Registry uses sqlite file at `VTX_APP_HOME/registry.sqlite` but tests should use temp path.
- [ ] Test syncing two projects and their clips; ensure registry reflects them.

Acceptance criteria:
- [ ] Multi-project registry sync works and is tested.

---

# Milestone E — Fixed schemas + validation utilities

## E1) Add schema validation helpers
Tasks:
- [ ] Add `vtx_app/story/validate.py`:
  - `validate_against_schema(data: dict, schema_path: Path) -> None`
  - Use `jsonschema` (recommended); fallback to minimal validation if not available.
- [ ] Validate:
  - outline yaml against `story.schema.json`
  - shotlist yaml against `shotlist.schema.json`
  - clip yaml against `clip.schema.json`

Tests:
- [ ] Validate a known-good fixture passes.
- [ ] Validate a broken fixture fails with clear message.

## E2) Enforce schema validation in the builder and loader
Tasks:
- [ ] After OpenAI writes outline/shotlist/clips, validate them.
- [ ] When loading clip specs for rendering, validate them before use.

Acceptance criteria:
- [ ] Schema validation errors include filename + path.

---

# Milestone F — OpenAI builder (Outline → Shotlist → Clip Specs)

## F1) Make OpenAI calls fully mockable
Tasks:
- [ ] Refactor `StoryBuilder` to accept an injected OpenAI client (default uses `OpenAI()`).
- [ ] Ensure `_call_structured(...)`:
  - always returns a dict matching schema
  - raises clear errors if JSON parse fails
  - logs the failing output text to a file under project logs (optional; but do not leak secrets)

Tests:
- [ ] Mock client `.responses.create()` returning predictable JSON.

## F2) Implement/finish generation functions
Tasks:
- [ ] `generate_outline()`:
  - reads `story/00_brief.md`
  - writes `story/01_outline.yaml`
  - validates schema
- [ ] `generate_shotlist()`:
  - uses outline + treatment (optional) to create `story/04_shotlist.yaml`
  - validates schema
- [ ] `generate_clip_specs()`:
  - reads shotlist
  - writes `prompts/clips/*.yaml`
  - supports filters: `--act`, `--scene`, `--overwrite`
  - validates each clip spec
  - ensures filename slug is deterministic

Tests:
- [ ] Outline generation writes file.
- [ ] Shotlist generation writes file.
- [ ] Clip generation writes expected number of clip yaml files with correct naming.

## F3) Consistency controls for OpenAI prompting
Tasks:
- [ ] Add “movie continuity” system instructions in prompts:
  - Always use keys from `characters.yaml` and `locations.yaml`.
  - Always refer to `style_bible` profile name.
- [ ] Add max characters / token budget enforcement:
  - If compiled prompts exceed a threshold, warn or split.

Tests:
- [ ] Ensure builder passes correct schema to the client.
- [ ] Ensure filters `--act/--scene` select correct subset.

Acceptance criteria:
- [ ] All generation paths testable without network.

---

# Milestone G — Continuity prompt compiler + LoRA bundles

## G1) Prompt compiler
Tasks:
- [ ] Ensure `compile_prompt(project, clip_spec)`:
  - loads `prompts/style_bible.yaml`
  - loads `prompts/characters.yaml` + `prompts/locations.yaml`
  - builds inserts for locked character/location descriptors
  - prepends the correct style prefix (global + profile)
  - combines negatives (global + profile + clip-specific)
  - returns a `PromptPack(positive, negative)` with clean whitespace

Tests:
- [ ] Golden tests:
  - given simple style bible + characters + locations + clip spec, the resulting prompt matches expected output exactly.
- [ ] Edge cases:
  - missing profile -> fallback to default
  - missing character key -> warning or include key name
  - empty negatives are handled cleanly

## G2) LoRA bundle resolver
Tasks:
- [ ] Implement `vtx_app/story/loras.py`:
  - load `prompts/loras.yaml`
  - allow named bundles (e.g., `core`, `flashback`)
  - resolve to concrete CLI args depending on pipeline type:
    - distilled lora args: `--distilled-lora <path> <weight>`
    - ic lora args: pipeline-specific flag(s)
- [ ] Ensure LoRA paths can reference:
  - explicit path
  - env var reference like `"env_path": "LTX_DISTILLED_LORA_PATH"`

Tests:
- [ ] Bundle resolves correctly.
- [ ] Missing env var triggers clear error.

Acceptance criteria:
- [ ] Continuity LoRAs are consistently applied across clips.

---

# Milestone H — Render controller (pipeline execution)

## H1) Finalize `render/renderer.py`
Tasks:
- [ ] Implement:
  - `RenderController.render_clip(clip_id)`
  - reading clip spec yaml
  - validating spec schema
  - compiling prompt via `compile_prompt`
  - determining duration/frames:
    - use `estimate_seconds(...)`
    - clamp to per-clip `max_seconds` and global `LTX_MAX_FRAMES`
  - building a `PipelineCommand` for the chosen pipeline
  - running via subprocess runner
  - updating registry state (planned → queued → rendering → rendered or rejected)
  - writing render metadata json (args, prompt hash, timestamps) to `renders/clips/*.render.json`

Tests:
- [ ] Mock the subprocess runner so no real pipeline runs.
- [ ] Ensure arguments are built correctly for `ti2vid_two_stages` (minimum required flags).
- [ ] Ensure failure updates `last_error` and state is `rejected`.

## H2) Pipeline module mapping
Tasks:
- [ ] Implement mapping from pipeline key → module string:
  - `ti2vid_two_stages` → `ltx_pipelines.ti2vid_two_stages`
  - `ti2vid_one_stage` → `ltx_pipelines.ti2vid_one_stage`
  - `distilled` → `ltx_pipelines.distilled`
  - `ic_lora` → `ltx_pipelines.ic_lora`
  - `keyframe_interpolation` → `ltx_pipelines.keyframe_interpolation`
- [ ] Validate pipeline key early with friendly error.
- [ ] Use `pipelines/capabilities.py` to add optional flags only when supported:
  - `--negative-prompt` or similar
  - `--width/--height`
  - `--fps`
  - `--num-frames`
  - `--seed`
  - input args for image/video/keyframes (detect via help)

Tests:
- [ ] Mock `detect_capabilities()` to return specific flags and assert the command includes them.

## H3) Input modalities (t2v/i2v/v2v/keyframes)
Tasks:
- [ ] Extend clip spec `inputs` handling:
  - `type: t2v` uses `--prompt` only
  - `type: i2v` uses `reference_image` flag (discover actual flag via `--help`)
  - `type: v2v` uses `input_video` flag (for `ic_lora`)
  - `type: keyframe_interpolation` uses keyframes list
- [ ] Add validations:
  - required input files exist
  - keyframes sorted and timecodes valid

Tests:
- [ ] For each input type, ensure the correct args are built when the module supports them (via mocked capabilities).

Acceptance criteria:
- [ ] Rendering works for all pipeline keys in a model-free test environment.

---

# Milestone I — Duration estimator (content-driven pacing)

## I1) Improve estimator logic (still deterministic)
Tasks:
- [ ] Expand heuristic mapping:
  - readable text props -> minimum hold time
  - dialogue -> minimum duration based on word count (approx)
  - camera moves (dolly, pan) -> add time
  - action beats count -> add time
- [ ] Ensure “as short as possible”:
  - estimator should err toward shorter durations unless keywords require longer
- [ ] Ensure clamping:
  - `seconds <= render.duration.max_seconds`
  - `frames <= LTX_MAX_FRAMES`

Tests:
- [ ] Table-driven tests for various prompts/beats producing expected seconds ranges.

Acceptance criteria:
- [ ] Estimator is predictable and fully tested.

---

# Milestone J — Assembler (acts + final) via ffmpeg

## J1) Implement `render/ffmpeg.py`
Tasks:
- [ ] Provide helpers to:
  - check ffmpeg availability (optional)
  - build concat demuxer list file
  - run ffmpeg concat command
- [ ] Do not require ffmpeg in unit tests; mock subprocess.

Tests:
- [ ] Validate correct concat file contents.
- [ ] Validate built ffmpeg command matches expected.

## J2) Implement `render/assembler.py`
Tasks:
- [ ] `assemble_act(project, act_number)`:
  - gather rendered clips for that act
  - create concat list in `renders/acts/`
  - output `renders/acts/A##.mp4`
- [ ] `assemble_final(project)`:
  - if acts mode enabled -> concat acts
  - else -> concat all scenes in order
  - output `renders/final/<slug>__final.mp4`
- [ ] Ordering rules:
  - sort by `clip_id` lexical (works with A##/S##/SH###)
  - or parse IDs to numeric sort for safety

Tests:
- [ ] Given fake rendered clip files, assembler chooses correct order and outputs correct target paths.

Acceptance criteria:
- [ ] Acts mode and final assembly are functional and tested.

---

# Milestone K — Multi-project “resume unfinished” orchestration

## K1) Resume command semantics
Tasks:
- [ ] `RenderController.resume(max_jobs=...)`:
  - queries registry for unfinished clips across all projects
  - prioritizes by `updated_at` or by act/scene order (define a rule)
  - renders up to `max_jobs`
- [ ] Add `--project` filter to resume command (optional) to resume a single project.

Tests:
- [ ] With two projects in registry, ensure resume selects correct clip set and calls `render_clip()`.

Acceptance criteria:
- [ ] Resume is stable and deterministic.

---

# Milestone L — Observability (logs, artifacts, reproducibility)

## L1) Logging
Tasks:
- [ ] Implement `utils/logging.py`:
  - configure Rich logging or stdlib logging
  - per-project logs in `projects/<slug>/logs/`
- [ ] Ensure subprocess stdout/stderr is captured:
  - store into `renders/clips/<clip>.log.txt` (optional)
  - store failure output in registry `last_error`

Tests:
- [ ] Mock runner returns stdout/stderr; verify log file written.

## L2) Reproducible render metadata
Tasks:
- [ ] Always write `.render.json` next to the mp4:
  - pipeline key + module
  - compiled prompts
  - LoRA bundle + weights
  - resolution/fps/frames/seed
  - environment snapshot (non-secret)
  - timestamps + duration
- [ ] Hashing:
  - compute a hash of all render inputs; if unchanged and mp4 exists, skip render.

Tests:
- [ ] If hash matches and output exists, renderer skips and updates registry accordingly.

---

# Milestone M — Documentation completeness

## M1) README finalization
Tasks:
- [ ] Document:
  - install steps
  - env files and layering
  - creating projects
  - generating story assets
  - rendering + resume
  - assembling acts/final
  - troubleshooting checklist (missing model paths, OpenAI key, ffmpeg missing)

## M2) Template project improvements
Tasks:
- [ ] Ensure template includes minimal examples:
  - `style_bible.yaml`, `characters.yaml`, `locations.yaml`, `loras.yaml`
  - minimal `00_brief.md`
  - example of one clip spec (optional)

Tests:
- [ ] A “create project then validate layout” test ensures template stays correct.

---

# Milestone N — Final polish + hardening

## N1) Robust error messages and UX
Tasks:
- [ ] Ensure every exception includes:
  - project slug
  - clip id (when applicable)
  - file paths involved
- [ ] Use Rich for readable output (colors, warnings).
- [ ] Add `vtx doctor` command (optional but recommended) that:
  - prints resolved env values (non-secret)
  - checks required files exist
  - checks ffmpeg available
  - checks projects discovered

Tests:
- [ ] `doctor` works in mocked environment.

## N2) Performance & RTX 4090 defaults
Tasks:
- [ ] Ensure default resolution/fps align with the shared env example:
  - 16fps, max 15s, width 1536 height 864 (16:9)
  - allow per-project override (e.g., 1920×800 for 2.39:1)
- [ ] Ensure clamping to max frames is always enforced.

Tests:
- [ ] A test that a 15s clip at 16fps yields 240 frames and is accepted; above 257 clamps.

---

## 4) Test plan (how to reach 100%)

### 4.1 Unit tests (fast)
- env layering and settings parsing
- registry CRUD and queries
- project template creation and validation
- schema validation helpers
- prompt compiler output
- lora resolver output
- duration estimator output
- pipeline args builder (capabilities mocked)
- render controller state transitions (subprocess mocked)
- assembler path ordering and ffmpeg command construction (subprocess mocked)
- CLI commands (Typer runner; mock heavy dependencies)

### 4.2 Integration tests (still model-free)
- “happy path” end-to-end with mocks:
  - create project → generate clip specs (mock OpenAI) → render one clip (mock subprocess) → assemble (mock ffmpeg)
- “resume” across two projects

### 4.3 Coverage mechanics
- Use `pytest-cov` fail-under=100.
- Mark unreachable OS-specific code with `# pragma: no cover` only when strictly needed.
- Keep functions small and injectable to make testing easy.

---

## 5) Notes for Codex (implementation guidance)

- Prefer incremental PRs/commits per milestone.
- Do not add network calls in tests; always mock OpenAI.
- Do not attempt real GPU rendering in tests.
- Keep formats stable: YAML files should always round-trip and stay schema-valid.
- When uncertain about pipeline flags, inspect via:
  - `python -m ltx_pipelines.<module> --help`
  - Then update the flag mapping logic + tests accordingly.
- Maintain backward compatibility of schemas (use `version: 1` and additive changes only).

---


## 6) Deliverables checklist (final)
- [ ] All milestones A → N complete
- [ ] `pytest --cov=vtx_app --cov-fail-under=100` passes
- [ ] CLI is complete and documented
- [ ] Multi-project resume works
- [ ] Acts mode works
- [ ] Outline/shotlist/clip generation works with schema enforcement
- [ ] Render orchestration works for all pipeline keys (when models exist)
- [ ] Assembly works (when ffmpeg exists)
- [ ] Docs are clear and accurate
