"""LLM orchestration for insurance claim investigation."""

import json
import urllib.error

from backend.llm.client import generate_with_ollama
from backend.llm.prompts import build_investigation_prompt
from backend.llm.validation import (
    build_citations,
    validate_response,
)


def generate_grounded_answer(
    query: str,
    evidence: list[dict],
    triggered_rules: list[dict],
    risk_score: int,
) -> dict:
    """
    Generate a grounded investigation report using Phi-3.

    Inputs:
        query:
            Investigator's natural-language question.

        evidence:
            Evidence retrieved by the upstream retrieval/RAG layer.

        triggered_rules:
            Rules already evaluated by the business-rule engine.

        risk_score:
            Risk score already calculated by the business-rule engine.

    Returns:
        A structured investigation response containing the generated
        report, query, and citations.
    """

    if not query.strip():
        return {
            "answer": "Please provide an insurance investigation query.",
            "query": query,
            "citations": [],
            "error": "empty_query",
        }

    prompt = build_investigation_prompt(
        query=query,
        evidence=evidence,
        triggered_rules=triggered_rules,
        risk_score=risk_score,
    )

    try:
        result = generate_with_ollama(prompt=prompt)

        raw_answer = result.get("response", "").strip()

        if not raw_answer:
            raise ValueError(
                "Phi-3 returned an empty response."
            )

        generated = json.loads(raw_answer)

        validated_answer = validate_response(
            generated=generated,
            evidence=evidence,
            triggered_rules=triggered_rules,
            risk_score=risk_score,
        )

        return {
            "answer": validated_answer,
            "query": query,
            "citations": build_citations(evidence),
        }

    except urllib.error.URLError as error:
        return {
            "answer": (
                "Unable to connect to the local Phi-3 model "
                "through Ollama."
            ),
            "query": query,
            "citations": [],
            "error": str(error),
        }

    except TimeoutError as error:
        return {
            "answer": (
                "The Phi-3 model took too long to respond."
            ),
            "query": query,
            "citations": [],
            "error": str(error),
        }

    except json.JSONDecodeError as error:
        return {
            "answer": (
                "Phi-3 returned an invalid JSON response."
            ),
            "query": query,
            "citations": [],
            "error": str(error),
        }

    except ValueError as error:
        return {
            "answer": (
                "Phi-3 returned an invalid or incomplete "
                "investigation response."
            ),
            "query": query,
            "citations": [],
            "error": str(error),
        }

    except Exception as error:
        return {
            "answer": (
                "An unexpected error occurred while generating "
                "the investigation response."
            ),
            "query": query,
            "citations": [],
            "error": str(error),
        }