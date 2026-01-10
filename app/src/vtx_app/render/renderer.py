from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from rich import print

from vtx_app.pipelines.base import PipelineCommand
from vtx_app.pipelines.capabilities import detect_capabilities, first_supported
from vtx_app.pipelines.runner_subprocess import run
from vtx_app.project.layout import Project
from vtx_app.registry.db import Registry
from vtx_app.render.presets import get_preset
from vtx_app.story.duration_estimator import estimate_seconds
from vtx_app.story.prompt_compiler import compile_prompt
from vtx_app.utils.timecode import now_iso
from vtx_app.utils.validation import validate_clip_spec

PIPELINE_MODULES = {
    "ti2vid_two_stages": "ltx_pipelines.ti2vid_two_stages",
    "ti2vid_one_stage": "ltx_pipelines.ti2vid_one_stage",
    "distilled": "ltx_pipelines.distilled",
    "ic_lora": "ltx_pipelines.ic_lora",
    "keyframe_interpolation": "ltx_pipelines.keyframe_interpolation",
}


@dataclass
class RenderController:
    project: Project | None
    registry: Registry

    def render_clip(self, *, clip_id: str, preset: str | None = None) -> None:
        if self.project is None:
            raise ValueError("RenderController.project is required for render_clip()")

        proj = self.project
        s = proj.settings()

        preset_cfg = get_preset(preset) if preset else {}

        clip_path = proj.root / "prompts" / "clips" / f"{clip_id}.yaml"
        if not clip_path.exists():
            # Try fuzzy match: clip_id prefix
            matches = list((proj.root / "prompts" / "clips").glob(f"{clip_id}__*.yaml"))
            if matches:
                clip_path = matches[0]
            else:
                raise FileNotFoundError(f"No clip spec found for {clip_id}")

        clip = yaml.safe_load(clip_path.read_text()) or {}

        # Validation
        validate_clip_spec(clip)

        pack = compile_prompt(project_root=proj.root, clip_spec=clip)

        out_rel = (clip.get("outputs") or {}).get("mp4")
        if not out_rel:
            raise ValueError(f"Clip spec missing outputs.mp4: {clip_path}")
        out_path = proj.root / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        pipeline_key = (clip.get("render") or {}).get("pipeline") or s.default_pipeline
        if pipeline_key not in PIPELINE_MODULES:
            raise KeyError(f"Unknown pipeline key: {pipeline_key}")
        module = PIPELINE_MODULES[pipeline_key]
        cap = detect_capabilities(module)

        # Resolution / fps defaults
        fps = int(
            preset_cfg.get("fps")
            or (clip.get("render") or {}).get("fps")
            or os.getenv("PROJECT_FPS")
            or s.default_fps
        )
        width = int(
            preset_cfg.get("width")
            or (clip.get("render") or {}).get("width")
            or os.getenv("PROJECT_WIDTH")
            or s.default_width
        )
        height = int(
            preset_cfg.get("height")
            or (clip.get("render") or {}).get("height")
            or os.getenv("PROJECT_HEIGHT")
            or s.default_height
        )

        # Duration -> frames (content-driven via story beats + prompt)
        seconds = estimate_seconds(clip)
        num_frames = int(round(seconds * fps))

        # Optional explicit override
        explicit_frames = (clip.get("render") or {}).get("num_frames")
        if isinstance(explicit_frames, int) and explicit_frames > 0:
            num_frames = explicit_frames

        num_frames = max(1, min(num_frames, s.ltx_max_frames))

        seed = (clip.get("render") or {}).get("seed")

        # Build args from env + clip + detected capabilities
        args: list[str] = []

        # Shared model paths
        if s.checkpoint_path:
            args += ["--checkpoint-path", s.checkpoint_path]
        if s.spatial_upsampler_path:
            args += ["--spatial-upsampler-path", s.spatial_upsampler_path]
        if s.gemma_root:
            args += ["--gemma-root", s.gemma_root]

        # LoRAs: prefer explicit clip loras, else fallback to shared distilled lora env
        # Clip schema supports: loras: [{env: "LTX_DISTILLED_LORA_PATH", weight: 0.8}, ...]
        loras = clip.get("loras") or []
        distilled_flag = first_supported(cap, "--distilled-lora", "--distilled_lora")
        if distilled_flag:
            if loras:
                for item in loras:
                    env_name = item.get("env")
                    weight = item.get("weight", 0.8)
                    if not env_name:
                        continue
                    path = os.getenv(env_name) or ""
                    if path:
                        args += [distilled_flag, path, str(weight)]
            elif s.distilled_lora_path:
                args += [distilled_flag, s.distilled_lora_path, "0.8"]

        # Optional controls (only if pipeline supports them)
        wflag = first_supported(cap, "--width")
        hflag = first_supported(cap, "--height")
        if wflag and hflag:
            args += [wflag, str(width), hflag, str(height)]

        fpsflag = first_supported(cap, "--fps", "--frame-rate", "--frame_rate")
        if fpsflag:
            args += [fpsflag, str(fps)]

        fflag = first_supported(cap, "--num-frames", "--num_frames", "--frames")
        if fflag:
            args += [fflag, str(num_frames)]

        sflag = first_supported(cap, "--seed")
        if sflag and isinstance(seed, int):
            args += [sflag, str(seed)]

        # Negative prompt (if supported)
        nflag = first_supported(cap, "--negative-prompt", "--negative_prompt")
        if nflag and pack.negative:
            args += [nflag, pack.negative]

        # Inputs (images/video)
        inputs = clip.get("inputs", {})

        # Reference image
        ref_img = inputs.get("reference_image")
        if ref_img:
            fpath = Path(ref_img)
            if not fpath.is_absolute():
                fpath = proj.root / ref_img

            # Warn if missing?
            if not fpath.exists():
                print(f"[yellow]Warning: Input image not found: {fpath}[/yellow]")

            img_flag = first_supported(cap, "--image")
            if img_flag:
                # Default: frame 0, strength 1.0
                args += [img_flag, str(fpath), "0", "1.0"]

        # Input video (video-to-video / ICLora)
        inp_vid = inputs.get("input_video")
        if inp_vid:
            fpath = Path(inp_vid)
            if not fpath.is_absolute():
                fpath = proj.root / inp_vid

            if not fpath.exists():
                print(f"[yellow]Warning: Input video not found: {fpath}[/yellow]")

            vid_flag = first_supported(
                cap, "--video-conditioning", "--video_conditioning"
            )
            if vid_flag:
                # Default strength 1.0
                args += [vid_flag, str(fpath), "1.0"]

        # Prompt + output
        pflag = first_supported(cap, "--prompt")
        if pflag:
            args += [pflag, pack.positive]
        else:
            # Most pipelines use --prompt; if not, fail loudly
            raise RuntimeError(
                f"Pipeline {module} appears to not support --prompt (detected flags: {sorted(cap.flags)[:20]})"
            )

        oflag = first_supported(cap, "--output-path", "--output_path")
        if oflag:
            args += [oflag, str(out_path)]
        else:
            args += ["--output-path", str(out_path)]

        cmd = PipelineCommand(module=module, args=args, output_path=out_path)

        # Registry state update
        meta = proj.load_metadata()
        project_id = str(meta.get("project_id"))
        self.registry.upsert_clip(
            project_id=project_id,
            clip_id=clip_id,
            state="rendering",
            output_path=str(out_path),
            render_hash=None,
            updated_at=now_iso(),
            last_error=None,
        )

        try:
            run(cmd)
            self.registry.upsert_clip(
                project_id=project_id,
                clip_id=clip_id,
                state="rendered",
                output_path=str(out_path),
                render_hash=None,
                updated_at=now_iso(),
                last_error=None,
            )
            print(
                f"[green]Rendered[/green] {clip_id} -> {out_rel}  ({seconds:.1f}s @ {fps}fps = {num_frames} frames)"
            )
        except Exception as e:
            self.registry.upsert_clip(
                project_id=project_id,
                clip_id=clip_id,
                state="rejected",
                output_path=str(out_path),
                render_hash=None,
                updated_at=now_iso(),
                last_error=str(e),
            )
            print(f"[red]Failed[/red] {clip_id}: {e}")
            if s.fail_fast:
                raise

    def resume(self, *, max_jobs: int = 1) -> None:
        """
        Naive resume: iterate registry unfinished clips and render them.
        This assumes projects + clips have been synced into the registry.
        """
        unfinished = self.registry.list_unfinished_clips()
        if not unfinished:
            print("[green]No unfinished clips.[/green]")
            return

        proj_map = {
            p["project_id"]: Path(p["path"]) for p in self.registry.list_projects()
        }

        count = 0
        for item in unfinished:
            if count >= max_jobs:
                break
            pid = item["project_id"]
            clip_id = item["clip_id"]
            proj_path = proj_map.get(pid)
            if not proj_path:
                continue
            proj = Project(root=proj_path)
            controller = RenderController(project=proj, registry=self.registry)
            controller.render_clip(clip_id=clip_id)
            count += 1
