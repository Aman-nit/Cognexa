"""Public interface for the Cognexa LLM module."""

from backend.llm.orchestration import generate_grounded_answer


__all__ = ["generate_grounded_answer"]