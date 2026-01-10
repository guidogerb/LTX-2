from __future__ import annotations

import typer
from rich import print

from vtx_app.config.log import configure_logging
from vtx_app.project.loader import ProjectLoader
from vtx_app.registry.db import Registry
from vtx_app.render.renderer import RenderController
from vtx_app.story.openai_builder import StoryBuilder

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    configure_logging(verbose=verbose)


projects_app = typer.Typer(no_args_is_help=True)
story_app = typer.Typer(no_args_is_help=True)
render_app = typer.Typer(no_args_is_help=True)
project_app = typer.Typer(no_args_is_help=True)
config_app = typer.Typer(no_args_is_help=True)

app.add_typer(projects_app, name="projects")
app.add_typer(story_app, name="story")
app.add_typer(render_app, name="render")
app.add_typer(project_app, name="project")
app.add_typer(config_app, name="config")


@app.command("clean")
def clean() -> None:
    """Clean global cache files (e.g. __pycache__)."""
    import shutil
    from pathlib import Path

    root = Path.cwd()
    count = 0
    for p in root.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p)
            count += 1
    print(f"[green]Removed {count} __pycache__ directories.[/green]")


@app.command("review")
def review(slug: str) -> None:
    """Open the assembled final_cut.mp4."""
    import os
    import shutil
    import subprocess
    import sys

    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    paths = [proj.root / "final_cut.mp4", proj.root / "storyboard.mp4"]
    found = None
    for p in paths:
        if p.exists():
            found = p
            break

    if not found:
        print(f"[red]No video found in {proj.root}[/red]")
        return

    print(f"Opening {found}...")
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(found)])
        elif sys.platform == "win32":
            os.startfile(found)
        else:
            # Linux
            if shutil.which("xdg-open"):
                subprocess.run(["xdg-open", str(found)])
            else:
                # Try creating a clickable link in terminal?
                print(f"File: [link=file://{found}]{found}[/link]")
    except Exception as e:
        print(f"[red]Failed to open: {e}[/red]")


@projects_app.command("list")
def projects_list() -> None:
    """List known projects (scans VTX_PROJECTS_ROOT and syncs registry)."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    loader.sync_all_projects()
    for p in reg.list_projects():
        print(f"[bold]{p['slug']}[/bold]  {p['title']}  (path={p['path']})")


@projects_app.command("new")
def projects_new(
    slug: str = typer.Argument(...),
    title: str = typer.Option(..., "--title"),
) -> None:
    """Create a new project from template."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    path = loader.create_project(slug=slug, title=title)
    print(f"[green]Created[/green] {slug} at {path}")


@project_app.command("env-create")
def project_env_create(slug: str) -> None:
    """Create a per-project virtualenv from that project's env/requirements.txt."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)
    proj.create_venv()
    print(f"[green]Env ready[/green] for {slug}: {proj.venv_path}")


@project_app.command("export")
def project_export(
    slug: str,
    output: str = typer.Option(None, "--output"),
) -> None:
    """Export project to a zip file (excluding .venv)."""
    import shutil
    import tempfile
    from pathlib import Path

    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    out_name = output or f"{slug}_export"
    if out_name.endswith(".zip"):
        out_name = out_name[:-4]

    with tempfile.TemporaryDirectory() as tmp_dir:
        dest = Path(tmp_dir) / slug
        shutil.copytree(
            proj.root,
            dest,
            ignore=shutil.ignore_patterns(
                ".venv", "__pycache__", ".git", ".DS_Store", "*.pyc"
            ),
        )

        archive = shutil.make_archive(
            base_name=out_name,
            format="zip",
            root_dir=tmp_dir,
            base_dir=slug,
        )
        print(f"[green]Exported[/green] to {archive}")


@story_app.command("outline")
def story_outline(slug: str) -> None:
    """Generate outline (01_outline.yaml) using OpenAI (optional)."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_outline()
    print("[green]Wrote[/green] story/01_outline.yaml")


@story_app.command("screenplay")
def story_screenplay(slug: str) -> None:
    """Generate screenplay (03_screenplay.yaml) using OpenAI."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_screenplay()
    print("[green]Wrote[/green] story/03_screenplay.yaml")


@story_app.command("characters")
def story_characters(slug: str) -> None:
    """Generate characters (prompts/characters.yaml) using OpenAI."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_characters()
    print("[green]Wrote[/green] prompts/characters.yaml")


@story_app.command("locations")
def story_locations(slug: str) -> None:
    """Generate locations (prompts/locations.yaml) using OpenAI."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_locations()
    print("[green]Wrote[/green] prompts/locations.yaml")


@story_app.command("shotlist")
def story_shotlist(slug: str) -> None:
    """Generate shotlist (04_shotlist.yaml) using OpenAI (optional)."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_shotlist()
    print("[green]Wrote[/green] story/04_shotlist.yaml")


@story_app.command("clips")
def story_clips(
    slug: str,
    act: int | None = typer.Option(None, "--act"),
    scene: int | None = typer.Option(None, "--scene"),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    """Generate per-clip specs under prompts/clips/ using OpenAI (optional)."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_clip_specs(overwrite=overwrite, act=act, scene=scene)
    print("[green]Generated[/green] prompts/clips/*.yaml")


@render_app.command("status")
def render_status(slug: str) -> None:
    """Show render status for project clips."""
    import yaml
    from rich import print
    from rich.table import Table

    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    table = Table(title=f"Render Status: {slug}")
    table.add_column("Clip ID", style="cyan")
    table.add_column("Output File", style="magenta")
    table.add_column("Status", justify="center")

    clips_dir = proj.root / "prompts" / "clips"
    if not clips_dir.exists():
        print(f"[yellow]No clips found in {clips_dir}[/yellow]")
        return

    for p in sorted(clips_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text()) or {}
            out_rel = (data.get("outputs") or {}).get("mp4")

            status = "[red]Missing output path[/red]"
            out_display = "---"

            if out_rel:
                out_path = proj.root / out_rel
                out_display = out_rel
                if out_path.exists():
                    status = "[green]Done[/green]"
                else:
                    status = "[yellow]Pending[/yellow]"

            table.add_row(p.stem, out_display, status)
        except Exception as e:
            table.add_row(p.stem, "Error", f"[red]{e}[/red]")

    print(table)


@render_app.command("clip")
def render_clip(
    slug: str,
    clip_id: str,
    preset: str = typer.Option(
        None, "--preset", help="Render profile: low, medium, high"
    ),
) -> None:
    """Render one clip by clip_id."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    controller = RenderController(project=proj, registry=reg)
    controller.render_clip(clip_id=clip_id, preset=preset)


@render_app.command("resume")
def render_resume(max_jobs: int = typer.Option(1, "--max-jobs")) -> None:
    """Resume unfinished clips across all projects."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    loader.sync_all_projects()

    controller = RenderController(project=None, registry=reg)
    controller.resume(max_jobs=max_jobs)


@render_app.command("assemble")
def render_assemble(
    slug: str, output: str = typer.Option("final_cut.mp4", "--output")
) -> None:
    """Concatenate all rendered clips into a final movie."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    from vtx_app.render.assembler import Assembler

    asm = Assembler(project=proj)
    asm.assemble(output_name=output)


@config_app.command("show")
def config_show(slug: str = typer.Option(None, "--project", "-p")) -> None:
    """Show effective settings. If project is set, includes project setup."""
    from dataclasses import asdict

    from vtx_app.config.env_layers import load_env
    from vtx_app.config.settings import Settings

    if slug:
        reg = Registry.load()
        loader = ProjectLoader(registry=reg)
        proj = loader.load(slug)
        load_env(project_env_path=proj.project_env_path)
    else:
        load_env()

    s = Settings.from_env()
    data = asdict(s)

    # Sanitize secrets
    # Assuming Settings might have it, though layout.py didn't show it in 30 lines.
    # checking if it exists before masking
    if "openai_api_key" in data:
        data["openai_api_key"] = "sk-..."

    print(data)
