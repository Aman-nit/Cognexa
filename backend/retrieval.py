"""Hybrid retrieval layer: combines SQL, BM25, FAISS, and editable rules."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def retrieve_evidence(query: str) -> list[dict[str, str]]:
    """Provide a deterministic starter result until indexes are built."""
    return [{"source": "query", "text": query, "status": "index not built"}]
