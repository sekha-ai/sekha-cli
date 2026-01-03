"""Sekha API client for CLI operations."""
import json
from typing import Any, Dict, List, Optional

from sekha import MemoryController, MemoryConfig


class SekhaClient:
    """Enhanced client for Sekha CLI operations."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.controller = MemoryController(
            MemoryConfig(base_url=base_url, api_key=api_key)
        )
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def query(self, query: str, label: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search conversations with semantic query."""
        try:
            response = self.controller.search(query, label=label, limit=limit)
            return response
        except Exception as e:
            raise RuntimeError(f"Query failed: {str(e)}") from e
    
    def store_conversation(self, file_path: str, label: str) -> Dict[str, Any]:
        """Store conversation from JSON file."""
        with open(file_path) as f:
            data = json.load(f)
        
        messages = data.get("messages", [])
        if not messages:
            raise ValueError("No messages found in file")
        
        result = self.controller.create(messages=messages, label=label)
        return {"id": result["id"], "label": label}
    
    def list_labels(self) -> List[Dict[str, Any]]:
        """List all labels with conversation counts."""
        # Get all conversations with empty query
        conversations = self.controller.search("", limit=1000)
        label_counts = {}
        
        for conv in conversations:
            label = conv.get("label", "Unknown")
            label_counts[label] = label_counts.get(label, 0) + 1
        
        return [{"name": name, "count": count} for name, count in sorted(label_counts.items())]

    def export(self, label: str, format: str = "markdown") -> str:
        """Export conversations by label."""
        # Get all conversations and filter by label
        all_conversations = self.controller.search("", limit=1000)
        conversations = [c for c in all_conversations if c.get("label") == label]
        
        if format == "markdown":
            return self._export_markdown(conversations)
        elif format == "json":
            return json.dumps(conversations, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get full conversation details."""
        return self.controller.get(conversation_id)
    
    def get_pruning_suggestions(self) -> List[Dict[str, Any]]:
        """Get pruning suggestions."""
        return self.controller.get_pruning_suggestions()
    
    def archive(self, conversation_id: str) -> None:
        """Archive a conversation."""
        self.controller.archive(conversation_id)
    
    def _export_markdown(self, conversations: List[Dict[str, Any]]) -> str:
        """Export conversations as markdown."""
        output = []
        
        for conv in conversations:
            output.append(f"# {conv.get('label', 'Unlabeled')}\n")
            output.append(f"**Created:** {conv.get('created_at', 'Unknown')}\n")
            output.append(f"**ID:** {conv.get('id')}\n\n")
            
            for msg in conv.get("messages", []):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                output.append(f"**{role.capitalize()}:** {content}\n\n")
            
            output.append("---\n\n")
        
        return "".join(output)