"""Erros de negócio e formato único de resposta de erro (docs/api/contrato-api.md §1)."""
import logging

import pymysql
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("nassau.erros")

RETRY_AFTER_SEG = "5"

_CODIGOS_HTTP = {
    401: "NAO_AUTENTICADO",
    403: "SEM_PERMISSAO",
    404: "NAO_ENCONTRADO",
    405: "METODO_NAO_PERMITIDO",
}


class ErroNegocio(Exception):
    """Erro previsto pelas regras do sistema. Sempre vira resposta no formato padrão."""

    def __init__(self, codigo: str, mensagem: str, status: int = 409, detalhes: dict | None = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.status = status
        self.detalhes = detalhes or {}


def resposta_erro(request: Request, codigo: str, mensagem: str, status: int,
                  detalhes: dict | None = None) -> JSONResponse:
    cabecalhos = {"Retry-After": RETRY_AFTER_SEG} if status == 503 else None
    return JSONResponse(
        status_code=status,
        headers=cabecalhos,
        content={
            "codigo": codigo,
            "mensagem": mensagem,
            "detalhes": detalhes or {},
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )


def _banco_indisponivel(request: Request) -> JSONResponse:
    return resposta_erro(request, "BANCO_INDISPONIVEL",
                         "Banco de dados indisponível. Tente novamente em instantes.", 503)


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroNegocio)
    async def _erro_negocio(request: Request, erro: ErroNegocio):
        return resposta_erro(request, erro.codigo, erro.mensagem, erro.status, erro.detalhes)

    @app.exception_handler(RequestValidationError)
    async def _validacao(request: Request, erro: RequestValidationError):
        campos = [
            {"campo": ".".join(str(parte) for parte in e["loc"] if parte != "body"), "mensagem": e["msg"]}
            for e in erro.errors()
        ]
        return resposta_erro(request, "VALIDACAO", "Corpo ou parâmetro inválido.", 422, {"campos": campos})

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, erro: StarletteHTTPException):
        codigo = _CODIGOS_HTTP.get(erro.status_code, f"HTTP_{erro.status_code}")
        return resposta_erro(request, codigo, str(erro.detail), erro.status_code)

    @app.exception_handler(pymysql.err.OperationalError)
    @app.exception_handler(pymysql.err.InterfaceError)
    async def _banco(request: Request, erro: Exception):
        logger.error("falha de banco de dados: %s", erro)
        return _banco_indisponivel(request)

    @app.exception_handler(Exception)
    async def _inesperado(request: Request, erro: Exception):
        logger.exception("erro inesperado")
        return resposta_erro(request, "ERRO_INTERNO", "Erro interno. Informe o request_id ao suporte.", 500)
