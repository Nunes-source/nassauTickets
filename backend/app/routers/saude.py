"""Health check (RF-18). Público."""
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.db import conectar
from app.core.errors import RETRY_AFTER_SEG
from app.repositories import saude as repo

router = APIRouter()
logger = logging.getLogger("nassau.saude")


class Saude(BaseModel):
    status: str
    banco: str


@router.get("/health", tags=["Saúde"], summary="Saúde do back end e do banco", response_model=Saude,
            description="200 se o banco responde a `SELECT 1`; 503 caso contrário.",
            responses={503: {"model": Saude, "description": "Banco fora do ar.",
                             "content": {"application/json": {"example": {"status": "degradado", "banco": "falha"}}}}})
def health():
    try:
        conn = conectar(esperas=())  # sem retry: o monitor quer a resposta rápida
        try:
            repo.ping(conn)
        finally:
            conn.close()
    except Exception:
        logger.exception("health check: banco indisponível")
        return JSONResponse(status_code=503, headers={"Retry-After": RETRY_AFTER_SEG},
                            content={"status": "degradado", "banco": "falha"})
    return {"status": "ok", "banco": "ok"}
