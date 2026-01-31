"""Vector store setup for RAG with FileSearchTool.

This module handles uploading knowledge base documents to OpenAI
and creating a vector store for semantic search.
"""

import os
from pathlib import Path
from openai import OpenAI

# Knowledge base documents directory
DOCS_DIR = Path(__file__).parent / "docs"

# Document files to upload
KNOWLEDGE_DOCS = [
    "return-policy.md",
    "pricing-guide.md",
    "troubleshooting.md",
    "escalation-criteria.md",
]


def get_openai_client() -> OpenAI:
    """Get OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def upload_documents(client: OpenAI) -> list[str]:
    """Upload knowledge base documents to OpenAI.

    Returns:
        List of file IDs for uploaded documents.
    """
    file_ids = []

    for doc_name in KNOWLEDGE_DOCS:
        doc_path = DOCS_DIR / doc_name

        if not doc_path.exists():
            print(f"Warning: {doc_name} not found, skipping")
            continue

        with open(doc_path, "rb") as f:
            response = client.files.create(
                file=f,
                purpose="assistants"
            )
            file_ids.append(response.id)
            print(f"Uploaded {doc_name} -> {response.id}")

    return file_ids


def create_vector_store(client: OpenAI, file_ids: list[str]) -> str:
    """Create a vector store with uploaded documents.

    Args:
        client: OpenAI client
        file_ids: List of file IDs to include

    Returns:
        Vector store ID
    """
    vector_store = client.vector_stores.create(
        name="customer-support-knowledge-base",
        file_ids=file_ids,
    )

    print(f"Created vector store: {vector_store.id}")
    return vector_store.id


def setup_knowledge_base() -> str:
    """Set up the complete knowledge base.

    Uploads documents and creates vector store.

    Returns:
        Vector store ID for use with FileSearchTool
    """
    client = get_openai_client()

    print("Uploading knowledge base documents...")
    file_ids = upload_documents(client)

    if not file_ids:
        raise ValueError("No documents were uploaded")

    print(f"\nCreating vector store with {len(file_ids)} documents...")
    vector_store_id = create_vector_store(client, file_ids)

    print(f"\nKnowledge base setup complete!")
    print(f"Vector Store ID: {vector_store_id}")
    print("\nAdd this to your agent configuration:")
    print(f'  FileSearchTool(vector_store_ids=["{vector_store_id}"])')

    return vector_store_id


def get_file_search_tool(vector_store_id: str):
    """Get a FileSearchTool configured with the knowledge base.

    Args:
        vector_store_id: ID of the vector store to search

    Returns:
        Configured FileSearchTool
    """
    from agents import FileSearchTool

    return FileSearchTool(
        vector_store_ids=[vector_store_id],
        max_num_results=5,
    )


if __name__ == "__main__":
    # Run setup when executed directly
    import sys

    try:
        vector_store_id = setup_knowledge_base()
        print(f"\n✓ Success! Vector store ID: {vector_store_id}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
