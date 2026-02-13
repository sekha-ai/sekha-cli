"""Sekha CLI - Command-line interface for Sekha AI Memory Controller."""
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

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
    """Sekha CLI v0.2.0 - Memory management from the command line."""
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


# ==================== SEARCH COMMANDS ====================

@cli.group()
def search():
    """Search operations (semantic and full-text)."""


@search.command("semantic")
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
def search_semantic(
    ctx: click.Context,
    query: str,
    label: Optional[str],
    limit: int,
    format: str,
):
    """Semantic search (embedding-based).

    Example:
        sekha search semantic "token limits" --label Work
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

            table = Table(title=f"🔍 Semantic Search: '{query}'")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Label", style="magenta")
            table.add_column("Preview", style="white")

            for r in results:
                preview = r.get("preview", r.get("content", ""))[:80] + "..."
                table.add_row(
                    r.get("id", r.get("conversation_id", ""))[:12],
                    r.get("label", "Unknown"),
                    preview,
                )

            console.print(table)

    except Exception as e:
        raise click.ClickException(f"Semantic search failed: {str(e)}") from e


@search.command("fts")
@click.argument("keywords")
@click.option("--limit", default=10, help="Max results", type=int)
@click.option(
    "--format",
    type=click.Choice(["json", "text"]),
    default="text",
    help="Output format",
)
@click.pass_context
def search_fts(
    ctx: click.Context,
    keywords: str,
    limit: int,
    format: str,
):
    """Full-text search (SQLite FTS5).

    Example:
        sekha search fts "embeddings AND llm"
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        results = client.full_text_search(keywords, limit=limit)

        if format == "json":
            click.echo(json.dumps(results, indent=2))
        else:
            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            table = Table(title=f"📝 Full-Text Search: '{keywords}'")
            table.add_column("Conversation", style="cyan")
            table.add_column("Role", style="magenta")
            table.add_column("Content", style="white")

            for r in results:
                content = r.get("content", "")[:100] + "..."
                table.add_row(
                    r.get("conversation_id", "unknown")[:12],
                    r.get("role", "unknown"),
                    content,
                )

            console.print(table)

    except Exception as e:
        raise click.ClickException(f"Full-text search failed: {str(e)}") from e


# ==================== LEGACY QUERY COMMAND (deprecated but kept for compatibility) ====================

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
    """[DEPRECATED] Use 'search semantic' instead.

    Example:
        sekha query "token limits" --label Work --limit 10
    """
    console.print("[yellow]⚠️  'query' is deprecated. Use 'search semantic' instead.[/yellow]\n")
    ctx.invoke(search_semantic, query=query, label=label, limit=limit, format=format)


# ==================== STORE COMMAND ====================

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
        console.print(f"[green]✅ Stored conversation: {result['id']}[/green]")

    except Exception as e:
        raise click.ClickException(f"Store failed: {str(e)}") from e


# ==================== CONVERSATION COMMANDS ====================

@cli.group()
def conversation():
    """Conversation operations (CRUD)."""


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


@conversation.command("delete")
@click.argument("conversation_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_conversation(
    ctx: click.Context,
    conversation_id: str,
    yes: bool,
):
    """Delete a conversation permanently.

    Example:
        sekha conversation delete <id> --yes
    """
    client: SekhaClient = ctx.obj["client"]

    if not yes:
        if not click.confirm(f"Delete conversation {conversation_id}?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    try:
        client.delete_conversation(conversation_id)
        console.print(f"[green]✅ Deleted conversation {conversation_id}[/green]")

    except Exception as e:
        raise click.ClickException(f"Delete failed: {str(e)}") from e


@conversation.command("pin")
@click.argument("conversation_id")
@click.pass_context
def pin_conversation(
    ctx: click.Context,
    conversation_id: str,
):
    """Pin a conversation (importance=10).

    Example:
        sekha conversation pin <id>
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        client.pin_conversation(conversation_id)
        console.print(f"[green]📌 Pinned conversation {conversation_id}[/green]")

    except Exception as e:
        raise click.ClickException(f"Pin failed: {str(e)}") from e


@conversation.command("archive")
@click.argument("conversation_id")
@click.pass_context
def archive_conversation(
    ctx: click.Context,
    conversation_id: str,
):
    """Archive a conversation.

    Example:
        sekha conversation archive <id>
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        client.archive(conversation_id)
        console.print(f"[green]📦 Archived conversation {conversation_id}[/green]")

    except Exception as e:
        raise click.ClickException(f"Archive failed: {str(e)}") from e


@conversation.command("count")
@click.option("--label", help="Count conversations with this label")
@click.option("--folder", help="Count conversations in this folder")
@click.pass_context
def count_conversations(
    ctx: click.Context,
    label: Optional[str],
    folder: Optional[str],
):
    """Count conversations.

    Example:
        sekha conversation count --label Work
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        result = client.count_conversations(label=label, folder=folder)
        
        count = result.get("count", 0)
        filter_type = "total"
        filter_value = "all conversations"
        
        if label:
            filter_type = "label"
            filter_value = label
        elif folder:
            filter_type = "folder"
            filter_value = folder
        
        console.print(Panel(
            f"[bold cyan]{count}[/bold cyan] conversations",
            title=f"Count: {filter_type} = {filter_value}",
            expand=False
        ))

    except Exception as e:
        raise click.ClickException(f"Count failed: {str(e)}") from e


# ==================== LABEL COMMANDS ====================

@cli.group()
def labels():
    """Label management and AI suggestions."""


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

        table = Table(title="🏷️  Labels")
        table.add_column("Label", style="cyan")
        table.add_column("Count", style="magenta", justify="right")

        for label in labels_list:
            table.add_row(label["name"], str(label["count"]))

        console.print(table)

    except Exception as e:
        raise click.ClickException(f"List labels failed: {str(e)}") from e


@labels.command("suggest")
@click.argument("conversation_id")
@click.option(
    "--format",
    type=click.Choice(["json", "text"]),
    default="text",
    help="Output format",
)
@click.pass_context
def suggest_labels(
    ctx: click.Context,
    conversation_id: str,
    format: str,
):
    """Get AI-powered label suggestions.

    Example:
        sekha labels suggest <conversation-id>
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        suggestions = client.suggest_labels(conversation_id)

        if format == "json":
            click.echo(json.dumps(suggestions, indent=2))
        else:
            if not suggestions:
                console.print("[yellow]No suggestions available.[/yellow]")
                return

            table = Table(title=f"🤖 AI Label Suggestions for {conversation_id[:12]}...")
            table.add_column("Label", style="cyan")
            table.add_column("Confidence", style="magenta", justify="right")
            table.add_column("Existing?", style="green")
            table.add_column("Reason", style="white")

            for s in suggestions:
                existing = "✅" if s.get("is_existing") else "🆕"
                confidence = f"{s.get('confidence', 0):.2f}"
                reason = s.get("reason", "No reason provided")[:50]
                
                table.add_row(
                    s.get("label", "Unknown"),
                    confidence,
                    existing,
                    reason,
                )

            console.print(table)

    except Exception as e:
        raise click.ClickException(f"Label suggestion failed: {str(e)}") from e


# ==================== FOLDER COMMANDS ====================

@cli.group()
def folder():
    """Folder management operations."""


@folder.command("list")
@click.pass_context
def list_folders(ctx: click.Context):
    """List all folders.

    Example:
        sekha folder list
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        folders = client.list_folders()

        if not folders:
            console.print("[yellow]No folders found.[/yellow]")
            return

        table = Table(title="📁 Folders")
        table.add_column("Folder", style="cyan")

        for f in folders:
            table.add_row(f)

        console.print(table)

    except Exception as e:
        raise click.ClickException(f"List folders failed: {str(e)}") from e


@folder.command("move")
@click.argument("conversation_id")
@click.argument("folder_path")
@click.pass_context
def move_conversation(
    ctx: click.Context,
    conversation_id: str,
    folder_path: str,
):
    """Move conversation to a folder.

    Example:
        sekha folder move <id> "/Work/Projects"
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        client.move_conversation(conversation_id, folder_path)
        console.print(f"[green]✅ Moved {conversation_id} to {folder_path}[/green]")

    except Exception as e:
        raise click.ClickException(f"Move failed: {str(e)}") from e


# ==================== CONTEXT & SUMMARIZATION ====================

@cli.command()
@click.argument("query")
@click.option("--budget", type=int, help="Token budget for context")
@click.option("--labels", multiple=True, help="Preferred labels (can specify multiple)")
@click.option("--exclude-folders", multiple=True, help="Folders to exclude")
@click.option(
    "--format",
    type=click.Choice(["json", "text"]),
    default="text",
    help="Output format",
)
@click.pass_context
def context(
    ctx: click.Context,
    query: str,
    budget: Optional[int],
    labels: tuple,
    exclude_folders: tuple,
    format: str,
):
    """Assemble relevant context for a query.

    Example:
        sekha context "explain embeddings" --budget 2000 --labels AI --labels ML
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        result = client.assemble_context(
            query=query,
            preferred_labels=list(labels) if labels else None,
            context_budget=budget,
            excluded_folders=list(exclude_folders) if exclude_folders else None,
        )

        if format == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            if not result:
                console.print("[yellow]No context found.[/yellow]")
                return

            console.print(Panel(
                f"[bold cyan]{len(result)}[/bold cyan] relevant messages",
                title=f"Context for: '{query}'",
                expand=False
            ))
            
            for i, msg in enumerate(result[:5], 1):  # Show first 5
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:200]
                console.print(f"\n{i}. [{role}] {content}...")
            
            if len(result) > 5:
                console.print(f"\n[dim]... and {len(result) - 5} more messages[/dim]")

    except Exception as e:
        raise click.ClickException(f"Context assembly failed: {str(e)}") from e


@cli.command()
@click.argument("conversation_id")
@click.option(
    "--level",
    type=click.Choice(["daily", "weekly", "monthly"]),
    required=True,
    help="Summary level",
)
@click.option(
    "--format",
    type=click.Choice(["json", "text", "markdown"]),
    default="text",
    help="Output format",
)
@click.pass_context
def summarize(
    ctx: click.Context,
    conversation_id: str,
    level: str,
    format: str,
):
    """Generate hierarchical summary.

    Example:
        sekha summarize <id> --level weekly --format markdown
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        with console.status(f"[bold cyan]Generating {level} summary..."):
            result = client.generate_summary(conversation_id, level)

        if format == "json":
            click.echo(json.dumps(result, indent=2))
        elif format == "markdown":
            summary_text = result.get("summary", "No summary generated")
            md = Markdown(summary_text)
            console.print(md)
        else:
            console.print(Panel(
                result.get("summary", "No summary generated"),
                title=f"{level.capitalize()} Summary - {conversation_id[:12]}...",
                border_style="cyan"
            ))

    except Exception as e:
        raise click.ClickException(f"Summarization failed: {str(e)}") from e


# ==================== PRUNING ====================

@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be pruned without doing it",
)
@click.option(
    "--yes",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.pass_context
def prune(ctx: click.Context, dry_run: bool, yes: bool):
    """Prune low-importance conversations.

    Example:
        sekha prune --dry-run
        sekha prune --yes
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        suggestions = client.get_pruning_suggestions()

        if not suggestions:
            console.print("[green]✅ No conversations need pruning.[/green]")
            return

        if dry_run:
            table = Table(title=f"[yellow]Would prune {len(suggestions)} conversations[/yellow]")
            table.add_column("ID", style="cyan")
            table.add_column("Label", style="magenta")
            table.add_column("Recommendation", style="yellow")
            
            for s in suggestions[:10]:  # Show first 10
                conv_id = s.get("conversation_id", "unknown")
                if isinstance(conv_id, str):
                    conv_id = conv_id[:12]
                else:
                    conv_id = str(conv_id)[:12]
                    
                table.add_row(
                    conv_id,
                    s.get("conversation_label", "Unknown"),
                    s.get("recommendation", "archive"),
                )
            
            console.print(table)
            
            if len(suggestions) > 10:
                console.print(f"[dim]... and {len(suggestions) - 10} more[/dim]")
        else:
            if not yes:
                if not click.confirm(f"Prune {len(suggestions)} conversations?"):
                    console.print("[yellow]Cancelled.[/yellow]")
                    return
            
            # Execute pruning
            conv_ids = [s.get("conversation_id") for s in suggestions]
            client.execute_pruning(conv_ids)
            console.print(f"[green]✅ Pruned {len(conv_ids)} conversations.[/green]")

    except Exception as e:
        raise click.ClickException(f"Prune failed: {str(e)}") from e


# ==================== EXPORT ====================

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
        console.print(f"[green]✅ Exported to {output}[/green]")

    except Exception as e:
        raise click.ClickException(f"Export failed: {str(e)}") from e


# ==================== HEALTH & MAINTENANCE ====================

@cli.command()
@click.pass_context
def health(ctx: click.Context):
    """Check controller health.

    Example:
        sekha health
    """
    client: SekhaClient = ctx.obj["client"]

    try:
        result = client.health_check()
        
        status = result.get("status", "unknown")
        version = result.get("version", "unknown")
        uptime = result.get("uptime_seconds", 0)
        
        status_color = "green" if status == "healthy" else "red"
        
        console.print(Panel(
            f"Status: [{status_color}]{status}[/{status_color}]\n"
            f"Version: {version}\n"
            f"Uptime: {uptime}s",
            title="🏥 Sekha Controller Health",
            border_style=status_color,
            expand=False
        ))

    except Exception as e:
        console.print(f"[red]❌ Health check failed: {str(e)}[/red]")
        raise click.ClickException("Controller appears to be down") from e


@cli.command()
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def rebuild_embeddings(ctx: click.Context, yes: bool):
    """Rebuild all embeddings (async operation).

    Example:
        sekha rebuild-embeddings --yes
    """
    client: SekhaClient = ctx.obj["client"]

    if not yes:
        if not click.confirm("Rebuild all embeddings? This may take a while."):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    try:
        client.rebuild_embeddings()
        console.print(
            "[green]✅ Embedding rebuild started (async).\n"
            "Check controller logs for progress.[/green]"
        )

    except Exception as e:
        raise click.ClickException(f"Rebuild failed: {str(e)}") from e


# ==================== CONFIG ====================

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
    """Configure default Sekha connection settings.
    
    Example:
        sekha config --api-url http://localhost:8080 --api-key your-key
    """
    config_obj = Config(base_url=api_url, api_key=api_key or "")

    try:
        config_obj.save()
        config_path = Config._get_default_config_path()
        console.print(f"[green]✅ Configuration saved to {config_path}[/green]")
    except Exception as e:
        raise click.ClickException(f"Config failed: {str(e)}") from e


if __name__ == "__main__":
    cli()
