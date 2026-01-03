"""Sekha CLI - Command-line interface for Sekha AI Memory Controller."""
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .client import SekhaClient
from .config import Config

console = Console()


@click.group()
@click.option(
    "--api-url",
    default="http://localhost:8080",
    envvar="SEKHA_API_URL",
    help="Sekha controller API URL",
)
@click.option(
    "--api-key",
    envvar="SEKHA_API_KEY",
    help="Sekha API key (can use SEKHA_API_KEY env var)",
)
@click.pass_context
def cli(ctx: click.Context, api_url: str, api_key: Optional[str]):
    """Sekha CLI - Memory management from the command line."""
    ctx.ensure_object(dict)

    # Try to load config if API key not provided
    if not api_key:
        try:
            config = Config.load()
            api_key = config.api_key
            api_url = config.base_url
        except FileNotFoundError:
            pass

    if not api_key:
        raise click.ClickException(
            "API key required. Set --api-key option or "
            "SEKHA_API_KEY environment variable"
        )

    ctx.obj["client"] = SekhaClient(base_url=api_url, api_key=api_key)


@cli.command()
@click.argument("query")
@click.option("--label", help="Filter by label")
@click.option("--limit", default=10, help="Max results", type=int)
@click.option(
    "--format",
    type=click.Choice(["json", "text"]),
    default="text",
    help="Output format",
)
@click.pass_context
def query(
    ctx: click.Context,
    query: str,
    label: Optional[str],
    limit: int,
    format: str,
):
    """Search conversations with semantic query.

    Example:
        sekha query "token limits" --label Work --limit 10
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        results = client.query(query, label=label, limit=limit)

        if format == "json":
            click.echo(json.dumps(results, indent=2))
        else:
            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            table = Table(title=f"Search: '{query}'")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Label", style="magenta")
            table.add_column("Preview", style="white")

            for r in results:
                preview = r.get("preview", "")[:100] + "..."
                table.add_row(
                    r.get("id", "")[:12],
                    r.get("label", ""),
                    preview,
                )

            console.print(table)

    except Exception as e:
        raise click.ClickException(f"Search failed: {str(e)}") from e


@cli.command()
@click.option(
    "--file",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="JSON file with conversation data",
)
@click.option("--label", required=True, help="Label for the conversation")
@click.pass_context
def store(ctx: click.Context, file: Path, label: str):
    """Store conversation from file.

    Example:
        sekha store --file conversation.json --label "Imported"
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        result = client.store_conversation(str(file), label)
        console.print(f"[green]Stored conversation: {result['id']}[/green]")

    except Exception as e:
        raise click.ClickException(f"Store failed: {str(e)}") from e


@cli.group()
def labels():
    """Manage conversation labels."""


@labels.command("list")
@click.pass_context
def list_labels(ctx: click.Context):
    """List all labels with conversation counts.

    Example:
        sekha labels list
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        labels_list = client.list_labels()

        if not labels_list:
            console.print("[yellow]No labels found.[/yellow]")
            return

        table = Table(title="Labels")
        table.add_column("Label", style="cyan")
        table.add_column("Count", style="magenta", justify="right")

        for label in labels_list:
            table.add_row(label["name"], str(label["count"]))

        console.print(table)

    except Exception as e:
        raise click.ClickException(f"List labels failed: {str(e)}") from e


@cli.group()
def conversation():
    """Conversation operations."""


@conversation.command("show")
@click.argument("conversation_id")
@click.option(
    "--format",
    type=click.Choice(["json", "markdown", "text"]),
    default="text",
    help="Output format",
)
@click.pass_context
def show_conversation(
    ctx: click.Context,
    conversation_id: str,
    format: str,
):
    """Show conversation details.

    Example:
        sekha conversation show <id> --format markdown
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        conv = client.get_conversation(conversation_id)

        if format == "json":
            click.echo(json.dumps(conv, indent=2))
        elif format == "markdown":
            console.print(f"# {conv.get('label', 'Unlabeled')}\n")
            for msg in conv.get("messages", []):
                role = msg.get("role", "unknown").capitalize()
                content = msg.get("content", "")
                console.print(f"**{role}:** {content}\n")
        else:
            console.print(f"Label: {conv.get('label', 'Unlabeled')}")
            console.print(f"Created: {conv.get('created_at', 'Unknown')}")
            console.print("\nMessages:")
            for msg in conv.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
                console.print(f"  {role}: {content}...")

    except Exception as e:
        raise click.ClickException(f"Show conversation failed: {str(e)}") from e


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be pruned without doing it",
)
@click.pass_context
def prune(ctx: click.Context, dry_run: bool):
    """Prune low-importance conversations.

    Example:
        sekha prune --dry-run
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        suggestions = client.get_pruning_suggestions()

        if not suggestions:
            console.print("[green]No conversations need pruning.[/green]")
            return

        if dry_run:
            msg = f"[yellow]Would prune {len(suggestions)} conversations:[/yellow]"
            console.print(msg)
            for s in suggestions:
                console.print(f"  - {s.get('id')}: {s.get('reason')}")
        else:
            if click.confirm(f"Prune {len(suggestions)} conversations?"):
                for s in suggestions:
                    client.archive(s.get("id"))
                console.print("[green]Pruning complete.[/green]")

    except Exception as e:
        raise click.ClickException(f"Prune failed: {str(e)}") from e


@cli.command()
@click.option(
    "--label",
    required=True,
    help="Export conversations with this label",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file path",
)
@click.option(
    "--format",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Export format",
)
@click.pass_context
def export(
    ctx: click.Context,
    label: str,
    output: Path,
    format: str,
):
    """Export conversations by label.

    Example:
        sekha export --label "Project:AI" --output backup.md
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        content = client.export(label, format=format)
        output.write_text(content)
        console.print(f"[green]Exported to {output}[/green]")

    except Exception as e:
        raise click.ClickException(f"Export failed: {str(e)}") from e


@cli.command()
@click.option(
    "--api-url",
    default="http://localhost:8080",
    help="Set default API URL",
)
@click.option(
    "--api-key",
    help="Set default API key",
)
def config(api_url: str, api_key: Optional[str]):
    """Configure default Sekha connection settings."""
    config_obj = Config(base_url=api_url, api_key=api_key or "")

    try:
        config_obj.save()
        config_path = Config._get_default_config_path()
        console.print(f"[green]Configuration saved to {config_path}[/green]")
    except Exception as e:
        raise click.ClickException(f"Config failed: {str(e)}") from e


if __name__ == "__main__":
    cli()
