"""Knowledge base for Customer Support FTE."""

from src.knowledge.vectorstore import (
    setup_knowledge_base,
    get_file_search_tool,
    DOCS_DIR,
    KNOWLEDGE_DOCS,
)

__all__ = [
    "setup_knowledge_base",
    "get_file_search_tool",
    "DOCS_DIR",
    "KNOWLEDGE_DOCS",
]
