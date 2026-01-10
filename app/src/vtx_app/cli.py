from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print

from vtx_app.config.env_layers import load_env
from vtx_app.config.log import configure_logging
from vtx_app.config.settings import Settings
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


@app.command("list-styles")
def list_styles() -> None:
    """List available styles in _global/styles."""
    from vtx_app.style_manager import StyleManager

    mgr = StyleManager()
    styles = mgr.list_styles()

    if not styles:
        print("[yellow]No styles found.[/yellow]")
        return

    print(f"[bold]Available Styles ({len(styles)}):[/bold]")
    for s in styles:
        print(f" - {s}")


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


@app.command("produce")
def produce(
    slug: str = typer.Argument(..., help="Project slug"),
    concept: str = typer.Option(
        ..., "--concept", "-c", help="Short story brief/concept"
    ),
    title: str = typer.Option(
        None, "--title", help="Project title (default: slugified)"
    ),
    render: bool = typer.Option(False, "--render", help="Immediately run rendering"),
) -> None:
    """Automated movie production (Zero to Finished)."""
    # Local import to avoid circular imports or early init
    from vtx_app.producer import Director

    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    director = Director(registry=reg, loader=loader)

    director.produce(slug=slug, concept=concept, title=title, auto_render=render)


@app.command("create-style")
def create_style(
    style_name: str = typer.Argument(..., help="Name of the new style"),
    project: Optional[str] = typer.Argument(
        None, help="Source project slug (default: current directory)"
    ),
) -> None:
    """
    Extract a reusable style style from an existing project.
    Usage: vtx create-style <style_name> [project_slug]
    """
    from vtx_app.style_manager import StyleManager

    slug = _get_slug(project)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    mgr = StyleManager()
    out_path = mgr.save_style(style_name, proj.root)
    print(f"[green]Style '{style_name}' saved to {out_path}[/green]")
    print(
        f'Use it in a new proposal: vtx create-movie new_movie "[{style_name}] my movie idea..."'
    )


@app.command("create-movie")
def create_movie(
    slug: str = typer.Argument(..., help="Name of the movie (project slug)"),
    prompt: str = typer.Argument(..., help="Prompt including concept, style, etc."),
) -> None:
    """Automated end-to-end creation flow: idea -> plan -> project -> story artifacts."""
    import shutil
    from pathlib import Path

    import yaml

    from vtx_app.config.settings import Settings
    from vtx_app.project.loader import ProjectLoader
    from vtx_app.registry.db import Registry
    from vtx_app.story.openai_builder import StoryBuilder
    from vtx_app.wizards.proposal import ProposalGenerator

    # 1. Proposal
    print(f"[bold blue]Step 1: Generating proposal for '{slug}'...[/bold blue]")
    s = Settings.from_env()
    gen = ProposalGenerator(settings=s)
    proposal = gen.create_proposal(prompt)

    # Force slug in proposal metadata to match argument
    if "meta" not in proposal:
        proposal["meta"] = {}
    proposal["meta"]["slug"] = slug

    plan_filename = f"{slug}_plan.yaml"
    plan_path = Path.cwd() / plan_filename
    plan_path.write_text(yaml.safe_dump(proposal, sort_keys=False))
    print(f"[green]Plan saved to {plan_path}[/green]")

    # 2. Create Project
    print(f"\n[bold blue]Step 2: Creating project from plan...[/bold blue]")
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)

    title = proposal["meta"].get("title", slug)
    try:
        path = loader.create_project(slug=slug, title=title)
        print(f"[green]Created project {slug}[/green] at {path}")
    except FileExistsError:
        print(f"[yellow]Project {slug} already exists, updating files...[/yellow]")
        proj = loader.load(slug)
        path = proj.root

    # Move plan file
    dest_plan = path / plan_filename
    if plan_path.resolve() != dest_plan.resolve():
        shutil.move(str(plan_path), str(dest_plan))
        print(f"Moved plan to {dest_plan}")

    # Write brief
    brief = proposal.get("story", {}).get("brief")
    if brief:
        (path / "story" / "00_brief.md").write_text(brief)
        print("Updated story/00_brief.md")

    # Hydrate Style Bible
    print("[blue]Generating Style Bible...[/blue]")
    proj = loader.load(slug)
    builder = StoryBuilder(project=proj)
    builder.generate_style_bible()
    print("Updated prompts/style_bible.yaml")

    # Update Resources (LoRAs)
    suggested_loras = proposal.get("resources", {}).get("suggested_loras", [])
    if suggested_loras:
        loras_file = path / "prompts" / "loras.yaml"
        current_loras = {}
        if loras_file.exists():
            current_loras = yaml.safe_load(loras_file.read_text()) or {}

        bundles = current_loras.get("bundles") or {}
        candidates = []
        for item in suggested_loras:
            candidates.append(
                {
                    "name": item["name"],
                    "url": item["url"],
                    "download_url": item["download_url"],
                    "trigger_word": "TODO",
                }
            )
        bundles["civitai_candidates"] = candidates
        current_loras["bundles"] = bundles
        loras_file.write_text(yaml.safe_dump(current_loras, sort_keys=False))
        print(f"Added {len(candidates)} LoRA candidates to prompts/loras.yaml")

    # 3. Story Generation Loop
    print(f"\n[bold blue]Step 3: Generating Story Artifacts...[/bold blue]")

    builder = StoryBuilder(project=proj)

    print("Generating Outline...")
    builder.generate_outline()
    print("[green]Wrote[/green] story/01_outline.yaml")

    print("Generating Treatment...")
    builder.generate_treatment()
    print("[green]Wrote[/green] story/02_treatment.md")

    print("Generating Shotlist...")
    builder.generate_shotlist()
    print("[green]Wrote[/green] story/04_shotlist.yaml")

    print("Generating Clip Specs...")
    builder.generate_clip_specs()
    print("[green]Generated[/green] prompts/clips/*.yaml")

    print(f"\n[bold green]Movie '{slug}' created successfully![/bold green]")
    print(f"Project location: {path}")
    print(f"Next step: cd projects/{slug}")


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


@projects_app.command("propose")
def projects_propose(
    concept: str = typer.Argument(..., help="Concept text or path to text file"),
    out: str = typer.Option("proposal.yaml", "--out", help="Output YAML file"),
) -> None:
    """Generate a project proposal with resource suggestions from CivitAI."""
    from pathlib import Path

    import yaml

    from vtx_app.config.settings import Settings
    from vtx_app.wizards.proposal import ProposalGenerator

    # Load concept text
    p = Path(concept)
    if p.exists() and p.is_file():
        text = p.read_text()
    else:
        text = concept

    s = Settings.from_env()
    gen = ProposalGenerator(settings=s)
    proposal = gen.create_proposal(text)

    # If out is default "proposal.yaml", try to use slug_plan.yaml
    meta = proposal.get("meta", {})
    slug = meta.get("slug")
    if out == "proposal.yaml" and slug:
        out = f"{slug}_plan.yaml"

    Path(out).write_text(yaml.safe_dump(proposal, sort_keys=False))
    print(f"[green]Proposal written to {out}[/green]")
    print(f"Edit this file, then run: vtx projects create-from-plan {out}")


@projects_app.command("create-from-plan")
def projects_create_from_plan(
    plan: str = typer.Argument(..., help="Path to proposal.yaml"),
) -> None:
    """Create a project and resources from a proposal file."""
    from pathlib import Path

    import yaml

    p = Path(plan)
    if not p.exists():
        print(f"[red]Plan file not found: {plan}[/red]")
        raise typer.Exit(1)

    data = yaml.safe_load(p.read_text()) or {}
    meta = data.get("meta", {})
    slug = meta.get("slug")
    title = meta.get("title")

    if not slug:
        print("[red]Missing meta.slug in plan[/red]")
        raise typer.Exit(1)

    # Create project
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    try:
        path = loader.create_project(slug=slug, title=title or slug)
        print(f"[green]Created project {slug}[/green] at {path}")
    except FileExistsError:
        print(f"[yellow]Project {slug} already exists, updating files...[/yellow]")
        proj = loader.load(slug)
        path = proj.root

    # Move the plan file to the project root
    dest_plan = path / p.name
    if p.resolve() != dest_plan.resolve():
        import shutil

        shutil.copy2(p, dest_plan)
        print(f"Copied plan to {dest_plan}")

    # Write brief
    brief = data.get("story", {}).get("brief")
    if brief:
        (path / "story" / "00_brief.md").write_text(brief)
        print("Updated story/00_brief.md")

    # Generate Style Bible (Hydrate from brief)
    from vtx_app.story.openai_builder import StoryBuilder

    builder = StoryBuilder(project=loader.load(slug))
    print("[blue]Generating Style Bible...[/blue]")
    builder.generate_style_bible()
    print("Updated prompts/style_bible.yaml")

    # Update resources/loras
    suggested_loras = data.get("resources", {}).get("suggested_loras", [])
    if suggested_loras:
        loras_file = path / "prompts" / "loras.yaml"
        current_loras = {}
        if loras_file.exists():
            current_loras = yaml.safe_load(loras_file.read_text()) or {}

        # Add suggestions to loras.yaml
        bundles = current_loras.get("bundles") or {}
        candidates = []
        for item in suggested_loras:
            candidates.append(
                {
                    "name": item["name"],
                    "url": item["url"],
                    "download_url": item["download_url"],
                    "trigger_word": "TODO",
                }
            )
        bundles["civitai_candidates"] = candidates
        current_loras["bundles"] = bundles

        loras_file.write_text(yaml.safe_dump(current_loras, sort_keys=False))
        print(f"Added {len(candidates)} LoRA candidates to prompts/loras.yaml")

    print("\n[bold]Next steps:[/bold]")
    print(f"1. cd projects/{slug}")
    print("2. vtx story outline")


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


def _get_slug(slug: str | None) -> str:
    if slug:
        return slug

    cwd = Path.cwd()
    load_env(project_env_path=None)
    s = Settings.from_env()

    try:
        rel = cwd.relative_to(s.projects_root.resolve())
    except ValueError:
        try:
            rel = cwd.relative_to(s.projects_root)
        except ValueError:
            print("[red]Missing argument 'SLUG'. Not in a project directory.[/red]")
            raise typer.Exit(code=1)

    if str(rel) == ".":
        print("[red]Missing argument 'SLUG'. Cannot infer from project root.[/red]")
        raise typer.Exit(code=1)

    inferred = rel.parts[0]
    print(f"[dim]Inferred project: {inferred}[/dim]")
    return inferred


@story_app.command("outline")
def story_outline(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate outline (01_outline.yaml) using OpenAI (optional)."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_outline()
    print("[green]Wrote[/green] story/01_outline.yaml")


@story_app.command("treatment")
def story_treatment(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate treatment (02_treatment.md) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_treatment()
    print("[green]Wrote[/green] story/02_treatment.md")


@story_app.command("screenplay")
def story_screenplay(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate screenplay (03_screenplay.yaml) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_screenplay()
    print("[green]Wrote[/green] story/03_screenplay.yaml")


@story_app.command("characters")
def story_characters(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate characters (prompts/characters.yaml) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_characters()
    print("[green]Wrote[/green] prompts/characters.yaml")


@story_app.command("locations")
def story_locations(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate locations (prompts/locations.yaml) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_locations()
    print("[green]Wrote[/green] prompts/locations.yaml")


@story_app.command("shotlist")
def story_shotlist(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate shotlist (04_shotlist.yaml) using OpenAI (optional)."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_shotlist()
    print("[green]Wrote[/green] story/04_shotlist.yaml")


@story_app.command("clips")
def story_clips(
    slug: Optional[str] = typer.Argument(None),
    act: int | None = typer.Option(None, "--act"),
    scene: int | None = typer.Option(None, "--scene"),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    """Generate per-clip specs under prompts/clips/ using OpenAI (optional)."""
    slug = _get_slug(slug)
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


@render_app.command("approve")
def render_approve(
    slug: str,
    clip_id: str,
    strategy: str = typer.Option("t2v", help="Final strategy: t2v or v2v"),
) -> None:
    """Mark a clip as approved and plan its final render strategy."""
    import yaml

    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    # Locate clip
    clip_path = proj.root / "prompts" / "clips" / f"{clip_id}.yaml"
    if not clip_path.exists():
        matches = list((proj.root / "prompts" / "clips").glob(f"{clip_id}__*.yaml"))
        if matches:
            clip_path = matches[0]
        else:
            print(f"[red]Clip {clip_id} not found[/red]")
            raise typer.Exit(1)

    data = yaml.safe_load(clip_path.read_text()) or {}

    # Check for draft output
    out_mp4 = (data.get("outputs") or {}).get("mp4")
    draft_exists = False
    if out_mp4:
        draft_exists = (proj.root / out_mp4).exists()

    if strategy == "v2v" and not draft_exists:
        print(
            f"[yellow]Warning: Strategy is v2v but no draft render found at {out_mp4}[/yellow]"
        )

    # Update metadata
    render_config = data.get("render") or {}
    render_config["approved"] = True
    render_config["final_strategy"] = strategy

    # If v2v, we might want to lock the input video path explicitly?
    # Or rely on convention (input = the draft output).
    # Let's rely on convention in renderer.

    data["render"] = render_config
    clip_path.write_text(yaml.safe_dump(data, sort_keys=False))
    print(f"[green]Approved[/green] {clip_id} for {strategy}")


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
