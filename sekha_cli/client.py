"""Sekha API client for CLI operations."""
import json
import requests
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
    
    # ==================== EXISTING METHODS ====================
    
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
    
    # ==================== NEW v0.2.0 METHODS ====================
    
    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation permanently.
        
        Args:
            conversation_id: UUID of conversation to delete
            
        Raises:
            RuntimeError: If deletion fails
        """
        url = f"{self.base_url}/api/v1/conversations/{conversation_id}"
        response = requests.delete(url, headers=self.headers, timeout=30)
        
        if response.status_code == 404:
            raise RuntimeError(f"Conversation {conversation_id} not found")
        elif response.status_code != 200:
            raise RuntimeError(f"Delete failed: {response.text}")
    
    def pin_conversation(self, conversation_id: str) -> None:
        """Pin a conversation (sets importance to 10).
        
        Args:
            conversation_id: UUID of conversation to pin
            
        Raises:
            RuntimeError: If pinning fails
        """
        url = f"{self.base_url}/api/v1/conversations/{conversation_id}/pin"
        response = requests.put(url, headers=self.headers, timeout=30)
        
        if response.status_code != 200:
            raise RuntimeError(f"Pin failed: {response.text}")
    
    def unpin_conversation(self, conversation_id: str) -> None:
        """Unpin a conversation (sets importance to 5).
        
        Note: Controller doesn't have explicit unpin endpoint,
        so we use update_importance directly.
        
        Args:
            conversation_id: UUID of conversation to unpin
            
        Raises:
            RuntimeError: If unpinning fails
        """
        # Use the controller's update method if available
        # For now, we'll document this as a limitation
        raise NotImplementedError(
            "Unpin not yet supported by controller API. "
            "Use 'sekha conversation update <id> --importance 5' when available."
        )
    
    def count_conversations(
        self, 
        label: Optional[str] = None, 
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """Count conversations, optionally filtered by label or folder.
        
        Args:
            label: Optional label to filter by
            folder: Optional folder to filter by
            
        Returns:
            Dict with 'count', 'label', 'folder' keys
            
        Raises:
            RuntimeError: If count fails
            ValueError: If both label and folder specified
        """
        if label and folder:
            raise ValueError("Cannot specify both label and folder")
        
        params = {}
        if label:
            params["label"] = label
        if folder:
            params["folder"] = folder
        
        url = f"{self.base_url}/api/v1/conversations/count"
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        
        if response.status_code != 200:
            raise RuntimeError(f"Count failed: {response.text}")
        
        return response.json()
    
    def full_text_search(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Full-text search using SQLite FTS5.
        
        Args:
            query: Search keywords (FTS5 syntax supported)
            limit: Maximum results to return
            
        Returns:
            List of matching messages with metadata
            
        Raises:
            RuntimeError: If search fails
        """
        url = f"{self.base_url}/api/v1/search/fts"
        payload = {
            "query": query,
            "limit": limit
        }
        
        response = requests.post(
            url, 
            headers=self.headers, 
            json=payload, 
            timeout=30
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"FTS search failed: {response.text}")
        
        data = response.json()
        return data.get("results", [])
    
    def assemble_context(
        self,
        query: str,
        preferred_labels: Optional[List[str]] = None,
        context_budget: Optional[int] = None,
        excluded_folders: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Assemble relevant context for a query.
        
        Args:
            query: Query to find relevant context for
            preferred_labels: Labels to prioritize
            context_budget: Token budget for context
            excluded_folders: Folders to exclude
            
        Returns:
            List of relevant messages
            
        Raises:
            RuntimeError: If context assembly fails
        """
        url = f"{self.base_url}/api/v1/context/assemble"
        payload = {
            "query": query,
            "preferred_labels": preferred_labels,
            "context_budget": context_budget,
            "excluded_folders": excluded_folders
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Context assembly failed: {response.text}")
        
        return response.json()
    
    def generate_summary(
        self,
        conversation_id: str,
        level: str
    ) -> Dict[str, Any]:
        """Generate hierarchical summary.
        
        Args:
            conversation_id: UUID of conversation to summarize
            level: Summary level - 'daily', 'weekly', or 'monthly'
            
        Returns:
            Summary response with summary text and metadata
            
        Raises:
            RuntimeError: If summarization fails
            ValueError: If invalid level
        """
        if level not in ["daily", "weekly", "monthly"]:
            raise ValueError(f"Invalid level: {level}. Must be daily, weekly, or monthly")
        
        url = f"{self.base_url}/api/v1/summarize"
        payload = {
            "conversation_id": conversation_id,
            "level": level
        }
        
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=60  # Summaries can take longer
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Summary generation failed: {response.text}")
        
        return response.json()
    
    def suggest_labels(
        self,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Get AI-powered label suggestions.
        
        Args:
            conversation_id: UUID of conversation to suggest labels for
            
        Returns:
            List of label suggestions with confidence scores
            
        Raises:
            RuntimeError: If suggestion fails
        """
        url = f"{self.base_url}/api/v1/labels/suggest"
        payload = {"conversation_id": conversation_id}
        
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Label suggestion failed: {response.text}")
        
        data = response.json()
        return data.get("suggestions", [])
    
    def execute_pruning(
        self,
        conversation_ids: List[str]
    ) -> None:
        """Execute pruning by archiving specified conversations.
        
        Args:
            conversation_ids: List of conversation UUIDs to archive
            
        Raises:
            RuntimeError: If pruning execution fails
        """
        url = f"{self.base_url}/api/v1/prune/execute"
        payload = {"conversation_ids": conversation_ids}
        
        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Prune execution failed: {response.text}")
    
    def list_folders(self) -> List[str]:
        """List all folders.
        
        Returns:
            List of folder names
            
        Note: This is implemented client-side by extracting folders
        from conversations since controller doesn't have dedicated endpoint.
        """
        # Get all conversations
        conversations = self.controller.search("", limit=1000)
        folders = set()
        
        for conv in conversations:
            folder = conv.get("folder")
            if folder:
                folders.add(folder)
        
        return sorted(list(folders))
    
    def move_conversation(
        self,
        conversation_id: str,
        folder: str
    ) -> None:
        """Move conversation to a different folder.
        
        Args:
            conversation_id: UUID of conversation to move
            folder: New folder path
            
        Raises:
            RuntimeError: If move fails
        """
        url = f"{self.base_url}/api/v1/conversations/{conversation_id}/folder"
        payload = {"folder": folder}
        
        response = requests.put(
            url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Move conversation failed: {response.text}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check controller health status.
        
        Returns:
            Health status with version and uptime info
            
        Raises:
            RuntimeError: If health check fails
        """
        url = f"{self.base_url}/health"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                raise RuntimeError(f"Health check failed: {response.text}")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Health check failed: {str(e)}") from e
    
    def rebuild_embeddings(self) -> None:
        """Rebuild all embeddings (async operation).
        
        This triggers an async rebuild process. Check logs for progress.
        
        Raises:
            RuntimeError: If rebuild trigger fails
        """
        url = f"{self.base_url}/api/v1/rebuild-embeddings"
        
        response = requests.post(url, headers=self.headers, timeout=30)
        
        if response.status_code != 202:  # Accepted
            raise RuntimeError(f"Rebuild embeddings failed: {response.text}")
