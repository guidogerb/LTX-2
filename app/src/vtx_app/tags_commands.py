import typer
from rich import print
from rich.table import Table
from vtx_app.tags_manager import TagManager

tags_app = typer.Typer(no_args_is_help=True)


def _get_manager():
    return TagManager()


@tags_app.command("list-groups")
def list_tag_groups():
    """List all available tag groups."""
    mgr = _get_manager()
    groups = mgr.list_groups()
    print("[bold]Available Tag Groups:[/bold]")
    for g in groups:
        print(f" - {g}")


@tags_app.command("list-all")
def list_tags_all():
    """List all tags in all groups."""
    mgr = _get_manager()
    data = mgr.list_tags()

    table = Table(title="All Tags")
    table.add_column("Group", style="cyan")
    table.add_column("Tag", style="green")
    table.add_column("Description", style="white")

    for group, tags in data.items():
        for tag in tags:
            details = mgr.load_tag(group, tag) or {}
            desc = details.get("meta", {}).get("description", "")
            table.add_row(group, tag, desc)

    print(table)


# Generic update command
def update_tag_desc_impl(group: str, tag: str, description: str):
    mgr = _get_manager()
    if mgr.update_description(group, tag, description):
        print(f"[green]Updated description for [{group}_{tag}][/green]")
    else:
        print(f"[red]Tag [{group}_{tag}] not found. Create it first.[/red]")


@tags_app.command("update-desc")
def update_tag_desc(
    group: str = typer.Argument(..., help="Tag group"),
    tag: str = typer.Argument(..., help="Tag name"),
    description: str = typer.Argument(..., help="New description"),
):
    """Update valid tag description."""
    update_tag_desc_impl(group, tag, description)


# Specific update commands generators
def make_update_command(group_name: str):
    def cmd(
        tag: str = typer.Argument(..., help="Tag name"),
        description: str = typer.Argument(..., help="New description"),
    ):
        """Update description for a tag in this group."""
        update_tag_desc_impl(group_name, tag, description)

    cmd.__name__ = f"update_{group_name.replace('-', '_')}_desc"
    return cmd
