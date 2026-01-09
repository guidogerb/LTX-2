from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml
from rich import print

from vtx_app.project.layout import Project
from vtx_app.registry.db import Registry
from vtx_app.story.prompt_compiler import compile_prompt
from vtx_app.pipelines.base import PipelineCommand
from vtx_app.pipelines.runner_subprocess import run
from vtx_app.utils.timecode import now_iso


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

    def render_clip(self, *, clip_id: str) -> None:
        assert self.project is not None
        proj = self.project
        s = proj.settings()

        # Load clip spec YAML
        clips_dir = proj.root / "prompts" / "clips"
        matches = list(clips_dir.glob(f"{clip_id}__*.yaml"))
        if not matches:
            raise FileNotFoundError(f"No clip spec for {clip_id} in {clips_dir}")
        clip_path = matches[0]
        clip = yaml.safe_load(clip_path.read_text())

        # Compile prompts
        pack = compile_prompt(project_root=proj.root, clip_spec=clip)

        # Output path
        out_rel = clip["outputs"]["mp4"]
        out_path = proj.root / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        pipeline_key = clip["render"]["pipeline"]
        module = PIPELINE_MODULES[pipeline_key]

        # Build args from env + clip
        args = []
        if s.checkpoint_path:
            args += ["--checkpoint-path", s.checkpoint_path]
        if s.distilled_lora_path:
            # Default weight from clip loras/bundles is not yet resolved here; keep simple.
            args += ["--distilled-lora", s.distilled_lora_path, "0.8"]
        if s.spatial_upsampler_path:
            args += ["--spatial-upsampler-path", s.spatial_upsampler_path]
        if s.gemma_root:
            args += ["--gemma-root", s.gemma_root]

        args += ["--prompt", pack.positive]
        args += ["--output-path", str(out_path)]

        cmd = PipelineCommand(module=module, args=args, output_path=out_path)

        self.registry.upsert_clip(
            project_id=proj.load_metadata().get("project_id"),
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
                project_id=proj.load_metadata().get("project_id"),
                clip_id=clip_id,
                state="rendered",
                output_path=str(out_path),
                render_hash=None,
                updated_at=now_iso(),
                last_error=None,
            )
            print(f"[green]Rendered[/green] {clip_id} -> {out_path}")
        except Exception as e:
            self.registry.upsert_clip(
                project_id=proj.load_metadata().get("project_id"),
                clip_id=clip_id,
                state="rejected",
                output_path=str(out_path),
                render_hash=None,
                updated_at=now_iso(),
                last_error=str(e),
            )
            raise

    def resume(self, *, max_jobs: int = 1) -> None:
        """
        Naive resume: iterate registry.unfinished clips and render them.
        Extend with job queue + priorities.
        """
        unfinished = self.registry.list_unfinished_clips()
        if not unfinished:
            print("[green]No unfinished clips.[/green]")
            return

        # map project_id -> path from projects table
        proj_map = {p["project_id"]: Path(p["path"]) for p in self.registry.list_projects()}

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
