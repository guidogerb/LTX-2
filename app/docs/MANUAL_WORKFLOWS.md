# Manual Workflows & Advanced Configuration

While the VTX CLI (`vtx`) provides automation for creating projects, stories, and rendering, many production scenarios require manual fine-tuning or custom workflows. This guide covers how to manually edit generated files, manage global templates, and invoke advanced rendering features.

## 1. Project Configuration

Each project is self-contained in `project/<project_slug>/`. The core configuration lives in two files:

### `metadata.yaml`
Defines the project defaults.
```yaml
title: "My Movie"
slug: "my_movie"
defaults:
  pipeline: "ti2vid_two_stages"  # Default rendering pipeline
  fps: 24
  aspect: "16:9"
  width: 1280
  height: 720
```
**Manual Edit**: Change `pipeline` here to `ltx_pipelines.distilled` or others to change the default for *new* clips.

### `project.env`
Environment variables specific to this project, overriding global defaults.
```bash
# Override model paths specific to this project
LTX_MODEL_PATH=/path/to/custom/checkpoint.safetensors
```

## 2. Managing Global Styles & Tags

VTX uses a centralized tag registry in `app/_global/tags/`. This allows you to share "styles", "character definitions" (if global), or other prompt fragments across projects.

### Anatomy of a Style File
Styles live in `app/_global/tags/style/<style_name>.yaml`.

**Example: `custom_noir.yaml`**
```yaml
meta:
  name: custom_noir
  description: "High contrast black and white film noir style"
resources:
  bundles:
    - name: "Noir LoRA"
      url: "https://civitai.com/models/..."
      trigger_word: "noir style"  # Clean this if just a placeholder
      weight: 0.8
```

### creating a New Style Group
To create a new category of tags (e.g., `camera_lenses`):

1. Create directory: `app/_global/tags/camera_lenses/`
2. Create tag files: `35mm.yaml`, `85mm.yaml`.
3. Valid structure:
   ```yaml
   meta:
     name: 35mm
   prompt: "shot on 35mm lens, wide field of view"
   ```

These can then be referenced in your prompt compiler or manually injected into clip prompts.

## 3. Manual Clip Creation & Modification

Clip specifications are generated in `project/<slug>/prompts/clips/`. Use these files to fine-tune individual shots.

### File Naming
Format: `<Act>_<Scene>_<ShotID>__<Slug>.yaml`
Example: `A01_S02_SH005__hero_enters.yaml`
*Note: The CLI fuzzy-matches files by ID, so the slug suffix is for human readability.*

### Clip Structure
```yaml
meta:
  id: "A01_S02_SH005"
  duration: 4.0

prompt:
  text: "RAW photo, 8k. The hero walks into the smoky bar..."
  negative: "blurry, low quality"

render:
  pipeline: "ti2vid_two_stages"  # Override default pipeline
  seed: 123456                   # Lock seed for reproducibility
  fps: 24
  resolution_scale: 1.0
  steps: 20
  
input:
  image: "assets/input_image.png" # For I2V pipelines
```

### How to Create a Clip Manually (Non-Linear Workflow)
If you want to render a test clip outside the story structure:

1. Create `project/<slug>/prompts/clips/TEST_001.yaml`.
2. Fill in the YAML structure above.
3. Run:
   ```bash
   vtx render clip <project_slug> TEST_001
   ```

## 4. Advanced: Using Alternative Pipelines

By default, LTX-2 uses `ti2vid_two_stages`. You can switch pipelines per clip to experiment with different models or speeds.

**Available Pipelines:**
* `ti2vid_two_stages`: Best quality, slower (Generation + Upscale).
* `ti2vid_one_stage`: Faster, standard resolution.
* `distilled`: Extremely fast (8 steps), good for prototyping.
* `ic_lora`: Image-conditioned/Video-to-Video.
* `keyframe_interpolation`: Smooth transitions between two images.

**To use a specific pipeline:**
In your clip YAML, set the `render.pipeline` field:
```yaml
render:
  pipeline: "distilled"
```

## 5. Reviewing and Assembling

After rendering:
1. `vtx render clip ...` produces `renders/clips/<id>/<version>/output.mp4`.
2. `vtx projects list` shows status.
3. Manual assembly:
   You can drag files from `renders/clips/` into Premiere/Resolve.
   OR use `vtx assemble final <slug>` to concatenate them based on `story/shotlist.yaml`.

If you manually added clips (TEST_001), they won't appear in the final assembly unless added to `story/04_shotlist.yaml`.

### Editing the Shotlist
`story/04_shotlist.yaml` drives the assembler.
```yaml
- id: A01_S01_SH001
  duration: 4.0
- id: TEST_001  # Manually added clip
  duration: 5.0
```
