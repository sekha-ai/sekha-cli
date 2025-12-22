import click
import json
from pathlib import Path
from sekha import MemoryController, MemoryConfig

@click.group()
@click.option('--api-url', default='http://localhost:8080', envvar='SEKHA_API_URL')
@click.option('--api-key', required=True, envvar='SEKHA_API_KEY')
@click.pass_context
def cli(ctx, api_url, api_key):
    """Sekha CLI - Memory management from the command line"""
    config = MemoryConfig(base_url=api_url, api_key=api_key)
    ctx.obj = MemoryController(config)

@cli.command()
@click.argument('query')
@click.option('--label', help='Filter by label')
@click.option('--limit', default=10, help='Max results')
@click.option('--format', type=click.Choice(['json', 'text']), default='text')
@click.pass_obj
def query(memory, query, label, limit, format):
    """Search conversations"""
    results = memory.search(query, label=label, limit=limit)
    
    if format == 'json':
        click.echo(json.dumps(results, indent=2))
    else:
        for r in results:
            click.echo(f"[{r['label']}] {r['id']}: {r['preview']}")

@cli.command()
@click.option('--file', type=click.Path(exists=True), required=True)
@click.option('--label', required=True)
@click.pass_obj
def store(memory, file, label):
    """Store conversation from file"""
    with open(file) as f:
        data = json.load(f)
    
    result = memory.create(messages=data['messages'], label=label)
    click.echo(f"Stored: {result['id']}")

@cli.group()
def labels():
    """Manage labels"""
    pass

@labels.command('list')
@click.pass_obj
def labels_list(memory):
    """List all labels"""
    labels = memory.list_labels()
    for label in labels:
        click.echo(f"{label['name']} ({label['count']} conversations)")

@cli.group()
def conversation():
    """Conversation operations"""
    pass

@conversation.command('show')
@click.argument('conversation_id')
@click.option('--format', type=click.Choice(['json', 'markdown', 'text']), default='text')
@click.pass_obj
def conversation_show(memory, conversation_id, format):
    """Show conversation details"""
    conv = memory.get_conversation(conversation_id)
    
    if format == 'json':
        click.echo(json.dumps(conv, indent=2))
    elif format == 'markdown':
        click.echo(f"# {conv['label']}\n\n")
        for msg in conv['messages']:
            click.echo(f"**{msg['role']}**: {msg['content']}\n")
    else:
        click.echo(f"Label: {conv['label']}")
        click.echo(f"Created: {conv['created_at']}")
        click.echo(f"\nMessages:")
        for msg in conv['messages']:
            click.echo(f"  {msg['role']}: {msg['content'][:100]}...")

@cli.command()
@click.option('--dry-run', is_flag=True, help='Show what would be pruned')
@click.pass_obj
def prune(memory, dry_run):
    """Prune low-importance conversations"""
    suggestions = memory.get_pruning_suggestions()
    
    if dry_run:
        click.echo(f"Would prune {len(suggestions)} conversations:")
        for s in suggestions:
            click.echo(f"  - {s['id']}: {s['reason']}")
    else:
        if click.confirm(f"Prune {len(suggestions)} conversations?"):
            for s in suggestions:
                memory.archive(s['id'])
            click.echo("Pruning complete")

@cli.command()
@click.option('--label', required=True)
@click.option('--output', type=click.Path(), required=True)
@click.option('--format', type=click.Choice(['markdown', 'json']), default='markdown')
@click.pass_obj
def export(memory, label, output, format):
    """Export conversations"""
    content = memory.export(label, format=format)
    Path(output).write_text(content)
    click.echo(f"Exported to {output}")

if __name__ == '__main__':
    cli()
