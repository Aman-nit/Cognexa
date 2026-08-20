"""Grounded response generation: local Phi-3/fallback orchestration and guardrails."""


def generate_grounded_answer(query: str, evidence: list[dict]) -> dict:
    """Return a safe starter response tied to retrieved evidence."""
    return {
        "answer": "Evidence retrieval is ready; configure a local Phi-3 model to generate an answer.",
        "query": query,
        "citations": [item.get("id", item.get("source", "unknown")) for item in evidence],
    }
