"""ClaimShield API entry point: exposes health and investigation routes."""

from fastapi import FastAPI
from pydantic import BaseModel

from backend.retrieval import retrieve_evidence

app = FastAPI(title="ClaimShield AI", version="0.1.0")


class InvestigationRequest(BaseModel):
    query: str


@app.get("/health")
def health() -> dict[str, str]:
    """Confirm that the API process is available."""
    return {"status": "ok"}


@app.post("/investigate")
def investigate(request: InvestigationRequest) -> dict:
    """Return evidence found for an investigator's natural-language query."""
    return {"query": request.query, "evidence": retrieve_evidence(request.query)}
