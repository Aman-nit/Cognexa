"""Reciprocal Rank Fusion utilities for merging retrieval result lists."""


def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Rank documents from multiple retrievers using reciprocal rank scores."""
    scores: dict[str, float] = {}
    documents: dict[str, dict] = {}
    for results in result_lists:
        for rank, document in enumerate(results, start=1):
            key = str(document.get("id", document.get("text", rank)))
            scores[key] = scores.get(key, 0.0) + 1 / (k + rank)
            documents[key] = document
    return [documents[key] for key in sorted(scores, key=scores.get, reverse=True)]
