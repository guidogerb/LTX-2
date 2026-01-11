from __future__ import annotations

import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from rich import print

from vtx_app.project.layout import Project
from vtx_app.project.loader import ProjectLoader
from vtx_app.registry.db import Registry
from vtx_app.render.assembler import Assembler
from vtx_app.story.openai_builder import StoryBuilder


@dataclass
class Director:
    registry: Registry
    loader: ProjectLoader

    def produce(
        self,
        slug: str,
        concept: str,
        title: str | None = None,
        auto_render: bool = False,
    ) -> None:
        """
        Orchestrates a full production from a brief concept.
        1. Creates project
        2. Generates story artifacts (brief -> outline -> treatment -> screenplay -> ...)
        3. Generates clip specs
        4. Generates a render script
        5. Optionally runs render
        """
        print(f"[bold green]🎬 Starting production for: {slug}[/bold green]")

        # 1. Create Project
        if not title:
            title = slug.replace("_", " ").title()

        # Check if exists
        try:
            proj = self.loader.load(slug)
            print(f"Project {slug} exists. Using existing.")
        except ValueError:
            path = self.loader.create_project(slug=slug, title=title)
            print(f"Created project at {path}")
            proj = self.loader.load(slug)

        # 2. Set Brief
        brief_path = proj.root / "story" / "00_brief.md"
        if not brief_path.exists() or brief_path.read_text().strip() == "":
            brief_path.write_text(concept)
            print(f"Wrote brief: {concept[:60]}...")
        else:
            print("Using existing brief.")

        builder = StoryBuilder(project=proj)

        # 3. Generate Artifacts (Chain)
        self._step("Outline", builder.generate_outline)
        self._step("Treatment", builder.generate_treatment)
        self._step("Screenplay", builder.generate_screenplay)
        self._step("Characters", builder.generate_characters)
        self._step("Locations", builder.generate_locations)
        self._step("Shotlist", builder.generate_shotlist)
        self._step("Clip Specs", builder.generate_clip_specs)

        # 4. Generate Render Script
        script_path = proj.root / "render_all.sh"
        self._generate_render_script(proj, script_path)
        print(f"[green]Generated render script:[/green] {script_path}")

        # 5. Auto Render?
        if auto_render:

            print("[bold red]🚀 Launching Render Sequence...[/bold red]")
            subprocess.run(["bash", str(script_path)], check=True)

            # Assemble
            asm = Assembler(project=proj)
            asm.assemble()
            print("[bold green]✅ Production Complete![/bold green] (final_cut.mp4)")

    def _step(self, name: str, func: Callable[[], None]) -> None:
        print(f"[cyan]Generating {name}...[/cyan]")
        try:
            func()
            print(f"[dim]Done {name}[/dim]")
        except Exception as e:
            print(f"[red]Failed {name}: {e}[/red]")

    def _generate_render_script(self, proj: Project, script_path: Path) -> None:
        """Writes a bash script to render all clips found in prompts/clips."""
        # Note: proj.slug doesn't exist on Project layout, assume metadata has it or pass it in.
        # But we assume calling code passed slug.
        # Actually proj is Project layout.

        # We need slug. Assuming proj.root.name is slug if not available.
        slug = proj.root.name

        lines = [
            "#!/bin/bash",
            "# Automated Render Script",
            "set -e",
            f"echo 'Rendering project: {slug}'",
            "",
            "# Ensure venv",
            f"source {proj.venv_path}/bin/activate || source {proj.venv_path}/Scripts/activate || true",
            "",
        ]

        # Find all clips
        clips_dir = proj.root / "prompts" / "clips"
        # We should check if clips exsit, BUT sometimes they are generated after
        # this script is written? No, we just generated them in step 3.
        # So we can search.
        clips = sorted(clips_dir.glob("*.yaml"))

        # If running in test, we might not have actual files unless mocked side effects created them.
        # But we want the script to be valid even if empty? No, render_all usually implies clips.
        # Let's trust glob.

        if not clips:
            lines.append("echo 'No clips found to render!'")
            # Fallback for test or empty run:
            # We add assemble anyway so at least we can verify it's there?
            # Or better: fix the test to create a dummy clip.
        else:
            for clip_path in clips:
                clip_id = clip_path.stem
                lines.append(f"echo 'Rendering {clip_id}...'")
                # We use the CLI command vtx render clip
                # Assuming 'vtx' is in path or we call python module
                lines.append(f"vtx render clip {slug} {clip_id}")

            lines.append("")
            lines.append("echo 'Assembling...'")
            lines.append(f"vtx render assemble {slug}")
            lines.append("echo 'Done.'")

        script_path.write_text("\n".join(lines))
        # Make executable
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
