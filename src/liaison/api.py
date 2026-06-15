"""Point d'entree FastAPI de Liaison : sante + chat (REST et SSE)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from liaison import __version__
from liaison.dependencies import get_audit_log, get_orchestrator, get_rbac_policy
from liaison.governance import (
    AccessDeniedError,
    AuditLog,
    Permission,
    Principal,
    RBACPolicy,
    mask_pii,
)
from liaison.logging import configure_logging
from liaison.orchestrator import Orchestrator
from liaison.schemas import AnswerResponse

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


class ChatRequest(BaseModel):
    """Requete de chat : question metier et role de l'appelant."""

    question: str = Field(min_length=1)
    role: str = "viewer"


def _principal(request: ChatRequest) -> Principal:
    return Principal(user_id="api-user", roles=frozenset({request.role}))


def _authorize_read(policy: RBACPolicy, principal: Principal, audit: AuditLog) -> None:
    try:
        policy.authorize(principal, Permission.READ_SQL)
        policy.authorize(principal, Permission.READ_DOCS)
    except AccessDeniedError as exc:
        audit.record(principal, action="chat", resource="orchestrator", allowed=False)
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Verifie que le service repond."""
    return HealthResponse(status="ok", version=__version__)


@app.post("/chat", response_model=AnswerResponse, tags=["chat"])
def chat(
    request: ChatRequest,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    policy: Annotated[RBACPolicy, Depends(get_rbac_policy)],
    audit: Annotated[AuditLog, Depends(get_audit_log)],
) -> AnswerResponse:
    """Repond a une question metier en orchestrant les connecteurs, sous controle RBAC."""
    principal = _principal(request)
    _authorize_read(policy, principal, audit)
    result = orchestrator.run(request.question)
    audit.record(principal, action="chat", resource="orchestrator", allowed=True)
    return result.model_copy(update={"answer": mask_pii(result.answer)})


@app.post("/chat/stream", tags=["chat"])
def chat_stream(
    request: ChatRequest,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    policy: Annotated[RBACPolicy, Depends(get_rbac_policy)],
    audit: Annotated[AuditLog, Depends(get_audit_log)],
) -> StreamingResponse:
    """Diffuse la reponse en SSE (un evenement par segment)."""
    principal = _principal(request)
    _authorize_read(policy, principal, audit)
    result = orchestrator.run(request.question)
    audit.record(principal, action="chat_stream", resource="orchestrator", allowed=True)
    answer = mask_pii(result.answer)

    def _events() -> Iterator[str]:
        for word in answer.split():
            yield f"data: {json.dumps({'token': word})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_events(), media_type="text/event-stream")
