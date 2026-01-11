from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich import print as rich_print
from rich.table import Table

from vtx_app.config.env_layers import load_env
from vtx_app.config.log import configure_logging
from vtx_app.config.settings import Settings
from vtx_app.producer import Director
from vtx_app.project.loader import ProjectLoader
from vtx_app.registry.db import Registry
from vtx_app.render.assembler import Assembler
from vtx_app.render.renderer import RenderController
from vtx_app.story.openai_builder import StoryBuilder
from vtx_app.style_manager import StyleManager
from vtx_app.tags_commands import tags_app
from vtx_app.wizards.proposal import ProposalGenerator

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
app.add_typer(tags_app, name="tags")


@app.command("clean")
def clean() -> None:
    """Clean global cache files (e.g. __pycache__)."""
    root = Path.cwd()
    count = 0
    for p in root.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p)
            count += 1
    rich_print(f"[green]Removed {count} __pycache__ directories.[/green]")


@app.command("list-styles")
def list_styles() -> None:
    """List available styles in _global/styles."""
    mgr = StyleManager()
    styles = mgr.list_styles()

    if not styles:
        rich_print("[yellow]No styles found.[/yellow]")
        return

    rich_print(f"[bold]Available Styles ({len(styles)}):[/bold]")
    for s in styles:
        data = mgr.load_style(s) or {}
        desc = data.get("meta", {}).get("description")
        if desc:
            rich_print(f" - [bold]{s}[/bold]: {desc}")
        else:
            rich_print(f" - {s}")


@app.command("review")
def review(slug: str) -> None:
    """Open the assembled final_cut.mp4."""
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
        rich_print(f"[red]No video found in {proj.root}[/red]")
        return

    rich_print(f"Opening {found}...")
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
    description: Optional[str] = typer.Argument(
        None, help="Optional description of the style"
    ),
) -> None:
    """
    Extract a reusable style style from an existing project.
    Usage: vtx create-style <style_name> [project_slug] [description]
    """
    slug = _get_slug(project)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    mgr = StyleManager()
    out_path = mgr.save_style(style_name, proj.root, description=description)

    rich_print(f"[green]Style '{style_name}' saved to {out_path}[/green]")
    rich_print(
        f'Use it in a new proposal: vtx create-movie new_movie "[{style_name}] my movie idea..."'
    )


@app.command("delete-style")
def delete_style(
    style_name: str = typer.Argument(..., help="Name of style to delete")
) -> None:
    """Deletes a style from the global style registry."""
    mgr = StyleManager()
    if mgr.delete_style(style_name):
        rich_print(f"[green]Style '{style_name}' deleted.[/green]")
    else:
        rich_print(f"[red]Style '{style_name}' not found.[/red]")


@app.command("update-style-desc")
def update_style_desc(
    style_name: str = typer.Argument(..., help="Name of the style"),
    description: str = typer.Argument(..., help="New description for the style"),
) -> None:
    """Updates the description of an existing style."""
    mgr = StyleManager()
    if mgr.update_description(style_name, description):
        rich_print(f"[green]Style '{style_name}' updated.[/green]")
    else:
        rich_print(f"[red]Style '{style_name}' not found.[/red]")


@app.command("render-reviews")
def render_reviews(
    slug: str = typer.Argument(..., help="Project slug"),
) -> None:
    """Renders all clips at half resolution to renders/low-res for review."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    clips_dir = proj.root / "prompts" / "clips"
    if not clips_dir.exists():
        rich_print(f"[red]No clips found in {slug}[/red]")
        return

    clip_files = sorted(clips_dir.glob("*.yaml"))

    # Filter out hidden files or non-yaml if glob isn't perfect
    clip_files = [p for p in clip_files if not p.name.startswith(".")]

    if not clip_files:
        rich_print(f"[red]No clips found in {slug}[/red]")
        return

    rich_print(f"Rendering {len(clip_files)} clips for review (low-res)...")

    controller = RenderController(project=proj, registry=reg)
    out_dir = proj.root / "renders" / "low-res"
    out_dir.mkdir(parents=True, exist_ok=True)

    for cf in clip_files:
        cid = cf.stem
        # Handle clip_id__desc format if necessary, though renderer handles fuzzy matching
        # But for list iteration we have exact file stem
        # Extract ID part if convention A01_S01__desc
        if "__" in cid:
            cid = cid.split("__")[0]

        rich_print(f"Rendering {cid}...")
        try:
            controller.render_clip(
                clip_id=cid, resolution_scale=0.5, output_dir=out_dir
            )
        except Exception as e:
            rich_print(f"[red]Failed to render {cid}: {e}[/red]")


@app.command("render-review")
def render_review(
    slug: str = typer.Argument(..., help="Project slug"),
    clip_name: str = typer.Argument(..., help="Clip ID/Name"),
) -> None:
    """Renders a single clip at half resolution to renders/low-res."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    controller = RenderController(project=proj, registry=reg)
    out_dir = proj.root / "renders" / "low-res"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clean clip name
    if "__" in clip_name:
        clip_name = clip_name.split("__")[0]

    rich_print(f"Rendering {clip_name} for review...")
    try:
        controller.render_clip(
            clip_id=clip_name, resolution_scale=0.5, output_dir=out_dir
        )
    except Exception as e:
        rich_print(f"[red]Failed to render {clip_name}: {e}[/red]")


@app.command("render-full")
def render_full(
    slug: str = typer.Argument(..., help="Project slug"),
) -> None:
    """Renders all clips at full resolution to renders/high-res."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    clips_dir = proj.root / "prompts" / "clips"
    if not clips_dir.exists():
        rich_print(f"[red]No clips found in {slug}[/red]")
        return

    clip_files = sorted(clips_dir.glob("*.yaml"))

    rich_print(f"Rendering {len(clip_files)} clips at FULL resolution...")

    controller = RenderController(project=proj, registry=reg)
    out_dir = proj.root / "renders" / "high-res"
    out_dir.mkdir(parents=True, exist_ok=True)

    for cf in clip_files:
        cid = cf.stem
        if "__" in cid:
            cid = cid.split("__")[0]

        rich_print(f"Rendering {cid}...")
        try:
            controller.render_clip(
                clip_id=cid, preset="final", resolution_scale=1.0, output_dir=out_dir
            )
        except Exception as e:
            print(f"[red]Failed to render {cid}: {e}[/red]")


@app.command("assemble")
def assemble(
    slug: str = typer.Argument(..., help="Project slug"),
) -> None:
    """Assembles clips from renders/high-res into final_cut.mp4."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    asm = Assembler(project=proj)
    high_res = proj.root / "renders" / "high-res"

    if high_res.exists():
        rich_print(f"Assembling from {high_res}...")
        asm.assemble(clips_dir=high_res)
    else:
        rich_print(
            "[yellow]High-res folder not found, assembling available clips...[/yellow]"
        )
        asm.assemble()


@app.command("create-movie")
def create_movie(
    slug: str = typer.Argument(..., help="Name of the movie (project slug)"),
    prompt: str = typer.Argument(..., help="Prompt including concept, style, etc."),
) -> None:
    """Automated end-to-end creation flow: idea -> plan -> project -> story artifacts."""
    # 1. Proposal
    rich_print(f"[bold blue]Step 1: Generating proposal for '{slug}'...[/bold blue]")
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
    rich_print(f"[green]Plan saved to {plan_path}[/green]")

    # 2. Create Project
    rich_print("\n[bold blue]Step 2: Creating project from plan...[/bold blue]")
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)

    title = proposal["meta"].get("title", slug)
    try:
        path = loader.create_project(slug=slug, title=title)
        rich_print(f"[green]Created project {slug}[/green] at {path}")
    except FileExistsError:
        rich_print(f"[yellow]Project {slug} already exists, updating files...[/yellow]")
        proj = loader.load(slug)
        path = proj.root

    # Move plan file
    dest_plan = path / plan_filename
    if plan_path.resolve() != dest_plan.resolve():
        shutil.move(str(plan_path), str(dest_plan))
        rich_print(f"Moved plan to {dest_plan}")

    # Write brief
    brief = proposal.get("story", {}).get("brief")
    if brief:
        (path / "story" / "00_brief.md").write_text(brief)
        rich_print("Updated story/00_brief.md")

    # Hydrate Style Bible
    rich_print("[blue]Generating Style Bible...[/blue]")
    proj = loader.load(slug)
    builder = StoryBuilder(project=proj)
    builder.generate_style_bible()
    rich_print("Updated prompts/style_bible.yaml")

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
        rich_print(f"Added {len(candidates)} LoRA candidates to prompts/loras.yaml")

    # 3. Story Generation Loop
    rich_print("\n[bold blue]Step 3: Generating Story Artifacts...[/bold blue]")

    builder = StoryBuilder(project=proj)

    rich_print("Generating Outline...")
    builder.generate_outline()
    rich_print("[green]Wrote[/green] story/01_outline.yaml")

    rich_print("Generating Treatment...")
    builder.generate_treatment()
    rich_print("[green]Wrote[/green] story/02_treatment.md")

    rich_print("Generating Shotlist...")
    builder.generate_shotlist()
    rich_print("[green]Wrote[/green] story/04_shotlist.yaml")

    rich_print("Generating Clip Specs...")
    builder.generate_clip_specs()
    rich_print("[green]Generated[/green] prompts/clips/*.yaml")

    rich_print(f"\n[bold green]Movie '{slug}' created successfully![/bold green]")
    rich_print(f"Project location: {path}")
    rich_print(f"Next step: cd projects/{slug}")


@app.command("create-movie-all")
def create_movie_all(
    slug: str = typer.Argument(..., help="Name of the movie (project slug)"),
    prompt: str = typer.Argument(..., help="Prompt including concept, style, etc."),
) -> None:
    """Automated end-to-end creation flow including rendering and assembly, bypassing reviews."""
    # Reuse create-movie logic logic but since create_movie is a command,
    # we can't easily call it directly if it has typer specific decorators/context,
    # or we can refactor. For now, duplication with extended steps is safer/clearer
    # given the prompt structure, or I can call it via a helper.
    # However, create_movie has heavy print logic. Let's replicate the flow.
    # 1. Proposal
    rich_print(f"[bold blue]Step 1: Generating proposal for '{slug}'...[/bold blue]")
    s = Settings.from_env()
    gen = ProposalGenerator(settings=s)
    proposal = gen.create_proposal(prompt)

    # Force slug in proposal metadata
    if "meta" not in proposal:
        proposal["meta"] = {}
    proposal["meta"]["slug"] = slug

    plan_filename = f"{slug}_plan.yaml"
    plan_path = Path.cwd() / plan_filename
    plan_path.write_text(yaml.safe_dump(proposal, sort_keys=False))
    print(f"[green]Plan saved to {plan_path}[/green]")

    # 2. Create Project
    print("\n[bold blue]Step 2: Creating project from plan...[/bold blue]")
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

    # Write brief
    brief = proposal.get("story", {}).get("brief")
    if brief:
        (path / "story" / "00_brief.md").write_text(brief)

    # Hydrate Style Bible
    print("[blue]Generating Style Bible...[/blue]")
    proj = loader.load(slug)
    builder = StoryBuilder(project=proj)
    builder.generate_style_bible()

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

    # 3. Story Generation Loop
    rich_print("\n[bold blue]Step 3: Generating Story Artifacts...[/bold blue]")
    builder = StoryBuilder(project=proj)

    rich_print("Generating Outline...")
    builder.generate_outline()
    rich_print("Generating Treatment...")
    builder.generate_treatment()
    rich_print("Generating Shotlist...")
    builder.generate_shotlist()
    rich_print("Generating Clip Specs...")
    builder.generate_clip_specs()
    # End of create-movie equivalent

    # 4. Render Full (Equivalent to render-full)
    rich_print("\n[bold blue]Step 4: Rendering Full Resolution...[/bold blue]")

    # Reload project to ensure paths are correct if things moved
    proj = loader.load(slug)

    clips_dir = proj.root / "prompts" / "clips"
    if not clips_dir.exists():
        rich_print(f"[red]No clips found in {slug}[/red]")
        return

    clip_files = sorted(clips_dir.glob("*.yaml"))
    # Debug print
    rich_print(f"DEBUG: Found clip files: {[p.name for p in clip_files]}")
    # Filter hidden
    clip_files = [p for p in clip_files if not p.name.startswith(".")]

    controller = RenderController(project=proj, registry=reg)
    out_dir = path / "renders" / "high-res"
    out_dir.mkdir(parents=True, exist_ok=True)

    for cf in clip_files:
        cid = cf.stem
        if "__" in cid:
            cid = cid.split("__")[0]

        rich_print(f"Rendering {cid} (Full Res)...")
        try:
            controller.render_clip(
                clip_id=cid, preset="final", resolution_scale=1.0, output_dir=out_dir
            )
        except Exception as e:
            rich_print(f"[red]Failed to render {cid}: {e}[/red]")

    # 5. Assemble (Equivalent to assemble)
    rich_print("\n[bold blue]Step 5: Assembling Final Cut...[/bold blue]")
    asm = Assembler(project=proj)

    if out_dir.exists():
        asm.assemble(clips_dir=out_dir)
    else:
        rich_print(
            "[yellow]High-res folder not found, attempting assembly of any available clips...[/yellow]"
        )
        asm.assemble()

    rich_print(f"\n[bold green]Movie '{slug}' COMPLETED![/bold green]")
    rich_print(f"Final video: {path}/final_cut.mp4")


@projects_app.command("list")
def projects_list() -> None:
    """List known projects (scans VTX_PROJECTS_ROOT and syncs registry)."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    loader.sync_all_projects()
    for p in reg.list_projects():
        rich_print(f"[bold]{p['slug']}[/bold]  {p['title']}  (path={p['path']})")


@projects_app.command("new")
def projects_new(
    slug: str = typer.Argument(...),
    title: str = typer.Option(..., "--title"),
) -> None:
    """Create a new project from template."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    path = loader.create_project(slug=slug, title=title)
    rich_print(f"[green]Created[/green] {slug} at {path}")


@projects_app.command("propose")
def projects_propose(
    concept: str = typer.Argument(..., help="Concept text or path to text file"),
    out: str = typer.Option("proposal.yaml", "--out", help="Output YAML file"),
) -> None:
    """Generate a project proposal with resource suggestions from CivitAI."""

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
    rich_print(f"[green]Proposal written to {out}[/green]")
    rich_print(f"Edit this file, then run: vtx projects create-from-plan {out}")


@projects_app.command("create-from-plan")
def projects_create_from_plan(
    plan: str = typer.Argument(..., help="Path to proposal.yaml"),
) -> None:
    """Create a project and resources from a proposal file."""

    p = Path(plan)
    if not p.exists():
        rich_print(f"[red]Plan file not found: {plan}[/red]")
        raise typer.Exit(1)

    data = yaml.safe_load(p.read_text()) or {}
    meta = data.get("meta", {})
    slug = meta.get("slug")
    title = meta.get("title")

    if not slug:
        rich_print("[red]Missing meta.slug in plan[/red]")
        raise typer.Exit(1)

    # Create project
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    try:
        path = loader.create_project(slug=slug, title=title or slug)
        rich_print(f"[green]Created project {slug}[/green] at {path}")
    except FileExistsError:
        rich_print(f"[yellow]Project {slug} already exists, updating files...[/yellow]")
        proj = loader.load(slug)
        path = proj.root

    # Move the plan file to the project root
    dest_plan = path / p.name
    if p.resolve() != dest_plan.resolve():
        shutil.copy2(p, dest_plan)
        rich_print(f"Copied plan to {dest_plan}")

    # Write brief
    brief = data.get("story", {}).get("brief")
    if brief:
        (path / "story" / "00_brief.md").write_text(brief)
        rich_print("Updated story/00_brief.md")

    # Generate Style Bible (Hydrate from brief)

    builder = StoryBuilder(project=loader.load(slug))
    rich_print("[blue]Generating Style Bible...[/blue]")
    builder.generate_style_bible()
    rich_print("Updated prompts/style_bible.yaml")

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
        rich_print(f"[green]Exported[/green] to {archive}")


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
            rich_print(
                "[red]Missing argument 'SLUG'. Not in a project directory.[/red]"
            )
            raise typer.Exit(code=1)

    if str(rel) == ".":
        rich_print(
            "[red]Missing argument 'SLUG'. Cannot infer from project root.[/red]"
        )
        raise typer.Exit(code=1)

    inferred = rel.parts[0]
    rich_print(f"[dim]Inferred project: {inferred}[/dim]")
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
    rich_print("[green]Wrote[/green] story/01_outline.yaml")


@story_app.command("treatment")
def story_treatment(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate treatment (02_treatment.md) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_treatment()
    rich_print("[green]Wrote[/green] story/02_treatment.md")


@story_app.command("screenplay")
def story_screenplay(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate screenplay (03_screenplay.yaml) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_screenplay()
    rich_print("[green]Wrote[/green] story/03_screenplay.yaml")


@story_app.command("characters")
def story_characters(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate characters (prompts/characters.yaml) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_characters()
    rich_print("[green]Wrote[/green] prompts/characters.yaml")


@story_app.command("locations")
def story_locations(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate locations (prompts/locations.yaml) using OpenAI."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_locations()
    rich_print("[green]Wrote[/green] prompts/locations.yaml")


@story_app.command("shotlist")
def story_shotlist(slug: Optional[str] = typer.Argument(None)) -> None:
    """Generate shotlist (04_shotlist.yaml) using OpenAI (optional)."""
    slug = _get_slug(slug)
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_shotlist()
    rich_print("[green]Wrote[/green] story/04_shotlist.yaml")


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
    rich_print("[green]Generated[/green] prompts/clips/*.yaml")


@render_app.command("status")
def render_status(slug: str) -> None:
    """Show render status for project clips."""

    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    table = Table(title=f"Render Status: {slug}")
    table.add_column("Clip ID", style="cyan")
    table.add_column("Output File", style="magenta")
    table.add_column("Status", justify="center")

    clips_dir = proj.root / "prompts" / "clips"
    if not clips_dir.exists():
        rich_print(f"[yellow]No clips found in {clips_dir}[/yellow]")
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

    rich_print(table)


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
            rich_print(f"[red]Clip {clip_id} not found[/red]")
            raise typer.Exit(1)

    data = yaml.safe_load(clip_path.read_text()) or {}

    # Check for draft output
    out_mp4 = (data.get("outputs") or {}).get("mp4")
    draft_exists = False
    if out_mp4:
        draft_exists = (proj.root / out_mp4).exists()

    if strategy == "v2v" and not draft_exists:
        rich_print(
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
    rich_print(f"[green]Approved[/green] {clip_id} for {strategy}")


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

    asm = Assembler(project=proj)
    asm.assemble(output_name=output)


@config_app.command("show")
def config_show(slug: str = typer.Option(None, "--project", "-p")) -> None:
    """Show effective settings. If project is set, includes project setup."""

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

    rich_print(data)
