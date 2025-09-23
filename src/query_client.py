# Re-export query() so orchestrator.py can do: from src import query_client
from src.app.quorum_query import query  # noqa: F401
