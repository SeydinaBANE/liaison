"""Point d'entree FastAPI de Liaison."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from liaison import __version__
from liaison.logging import configure_logging

configure_logging()

app = FastAPI(
    title="Liaison",
    version=__version__,
    description="Hub d'integration GenAI pour systemes d'information existants.",
)


class HealthResponse(BaseModel):
    """Reponse du endpoint de sante."""

    status: str
    version: str


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Verifie que le service repond."""
    return HealthResponse(status="ok", version=__version__)
