"""Point d'entree FastAPI de Liaison : sante + chat (REST et SSE)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from liaison import __version__
from liaison.adapters.inbound.http.dependencies import (
    get_audit_log,
    get_orchestrator,
    get_principal,
    get_rbac_policy,
)
from liaison.adapters.inbound.http.middleware import setup_middlewares
from liaison.application.orchestrator import Orchestrator
from liaison.domain.audit import AuditLog
from liaison.domain.models import AnswerResponse
from liaison.domain.pii import mask_pii
from liaison.domain.rbac import (
    AccessDeniedError,
    Permission,
    Principal,
    RBACPolicy,
)
from liaison.platform.config import get_settings
from liaison.platform.logging import configure_logging, get_logger

logger = get_logger(__name__)
configure_logging()


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
    yield
    from liaison.services import _cleanup

    await _cleanup()


app = FastAPI(
    title="Liaison",
    version=__version__,
    description="Hub d'integration GenAI pour systemes d'information existants.",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    """Reponse du endpoint de sante."""

    status: str
    version: str


class ChatRequest(BaseModel):
    """Requete de chat : question metier."""

    question: str = Field(min_length=1, max_length=2000)


def _authorize_read(policy: RBACPolicy, principal: Principal, audit: AuditLog) -> None:
    try:
        policy.authorize(principal, Permission.READ_SQL)
        policy.authorize(principal, Permission.READ_DOCS)
    except AccessDeniedError as exc:
        audit.record(principal.user_id, action="chat", resource="orchestrator", allowed=False)
        raise HTTPException(status_code=403, detail="acces refuse") from exc


def _safe_error(exc: Exception) -> HTTPException:
    """Convertit une erreur interne en HTTPException sans fuite d'information."""
    logger.error("internal_error", error=str(exc), error_type=type(exc).__name__)
    return HTTPException(status_code=500, detail="erreur interne")


_cfg = get_settings()
_cors_origins = _cfg.env.lower() == "local" and "*" or ""
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_middlewares(app, _cfg.rate_limit_max_requests, _cfg.rate_limit_window_sec)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Verifie que le service repond."""
    return HealthResponse(status="ok", version=__version__)


@app.post("/chat", response_model=AnswerResponse, tags=["chat"])
async def chat(
    request: ChatRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    policy: Annotated[RBACPolicy, Depends(get_rbac_policy)],
    audit: Annotated[AuditLog, Depends(get_audit_log)],
) -> AnswerResponse:
    """Repond a une question metier en orchestrant les connecteurs, sous controle RBAC."""
    _authorize_read(policy, principal, audit)
    result = await orchestrator.run(request.question)
    audit.record(principal.user_id, action="chat", resource="orchestrator", allowed=True)
    return result.model_copy(update={"answer": mask_pii(result.answer)})


@app.post("/chat/stream", tags=["chat"])
async def chat_stream(
    request: ChatRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    policy: Annotated[RBACPolicy, Depends(get_rbac_policy)],
    audit: Annotated[AuditLog, Depends(get_audit_log)],
) -> StreamingResponse:
    """Diffuse la reponse en SSE (un evenement par segment)."""
    _authorize_read(policy, principal, audit)
    audit.record(principal.user_id, action="chat_stream", resource="orchestrator", allowed=True)

    async def _events() -> AsyncIterator[str]:
        async for event in orchestrator.run_stream(request.question):
            yield event

    return StreamingResponse(_events(), media_type="text/event-stream")


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Attrape les exceptions non gerees pour eviter les fuites d'information."""
    if isinstance(exc, HTTPException):
        raise
    logger.error("unhandled_exception", error=str(exc), error_type=type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "erreur interne"})
