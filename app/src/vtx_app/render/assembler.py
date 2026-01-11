from __future__ import annotations

from pathlib import Path

import yaml
from rich import print

from vtx_app.project.layout import Project
from vtx_app.render.ffmpeg import concat_videos


class Assembler:
    def __init__(self, project: Project):
        self.project = project

    def assemble(
        self, output_name: str = "final_cut.mp4", clips_dir: Path | None = None
    ) -> None:
        """
        Scans story/04_shotlist.yaml, finds rendered clips, and concatenates them.
        """
        shotlist_path = self.project.root / "story" / "04_shotlist.yaml"
        if not shotlist_path.exists():
            raise FileNotFoundError("Missing story/04_shotlist.yaml")

        data = yaml.safe_load(shotlist_path.read_text()) or {}
        scenes = data.get("scenes", [])

        clip_files = []
        missing_clips = []

        for sc in scenes:
            shots = sc.get("shots", [])
            for sh in shots:
                cid = sh.get("clip_id")
                if not cid:
                    continue

                # Check for rendered mp4
                # We need to find the definition file first to know where the output goes?
                # Or we can just look in renders/clips/*.mp4 if we follow convention.
                # Convention: prompts/clips/{cid}__*.yaml -> renders/clips/{cid}__*.mp4

                # Let's look up the clip spec to be sure
                matches = list(
                    (self.project.root / "prompts" / "clips").glob(f"{cid}__*.yaml")
                )
                if not matches:
                    missing_clips.append(f"{cid} (spec missing)")
                    continue

                # Read spec to find output path logic, or just assume convention
                spec = yaml.safe_load(matches[0].read_text())
                out_leaf = spec.get("outputs", {}).get("mp4")
                if out_leaf:
                    mp4_path = self.project.root / out_leaf

                    # Override lookup if clips_dir is provided
                    if clips_dir:
                        # Try to find the file in clips_dir with the same name
                        override_path = clips_dir / mp4_path.name
                        if override_path.exists():
                            mp4_path = override_path

                    if mp4_path.exists():
                        clip_files.append(mp4_path)
                    else:
                        missing_clips.append(f"{cid} (not rendered: {mp4_path})")
                else:
                    missing_clips.append(f"{cid} (no output path)")

        if missing_clips:
            print(
                "[yellow]Warning: The following clips are missing and will be skipped:[/yellow]"
            )
            for m in missing_clips:
                print(f"  - {m}")

        if not clip_files:
            print("[red]No clips found to assemble.[/red]")
            return

        out_path = self.project.root / "renders" / output_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"[green]Assembling[/green] {len(clip_files)} clips to {out_path}...")
        concat_videos(clip_files, out_path)
        print("[bold green]Done![/bold green]")
