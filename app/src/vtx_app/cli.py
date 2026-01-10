from __future__ import annotations

import typer
from rich import print

from vtx_app.project.loader import ProjectLoader
from vtx_app.registry.db import Registry
from vtx_app.render.renderer import RenderController
from vtx_app.story.openai_builder import StoryBuilder

app = typer.Typer(no_args_is_help=True)

projects_app = typer.Typer(no_args_is_help=True)
story_app = typer.Typer(no_args_is_help=True)
render_app = typer.Typer(no_args_is_help=True)
project_app = typer.Typer(no_args_is_help=True)

app.add_typer(projects_app, name="projects")
app.add_typer(story_app, name="story")
app.add_typer(render_app, name="render")
app.add_typer(project_app, name="project")


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


@story_app.command("outline")
def story_outline(slug: str) -> None:
    """Generate outline (01_outline.yaml) using OpenAI (optional)."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    builder = StoryBuilder(project=proj)
    builder.generate_outline()
    print("[green]Wrote[/green] story/01_outline.yaml")


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


@render_app.command("clip")
def render_clip(slug: str, clip_id: str) -> None:
    """Render one clip by clip_id."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    proj = loader.load(slug)

    controller = RenderController(project=proj, registry=reg)
    controller.render_clip(clip_id=clip_id)


@render_app.command("resume")
def render_resume(max_jobs: int = typer.Option(1, "--max-jobs")) -> None:
    """Resume unfinished clips across all projects."""
    reg = Registry.load()
    loader = ProjectLoader(registry=reg)
    loader.sync_all_projects()

    controller = RenderController(project=None, registry=reg)
    controller.resume(max_jobs=max_jobs)
