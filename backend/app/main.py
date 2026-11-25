"""Ponto de entrada da API nassauTickets."""
import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

from app.core.config import get_config
from app.core.errors import registrar_handlers
from app.core.logging import configurar_logging, middleware_requisicao
from app.routers import auth, cadastros, relatorios, saude

PREFIXO = "/api/v1"

TAGS = [
    {"name": "Autenticação", "description": "Login e dados do usuário logado."},
    {"name": "Guichês", "description": "Listar, ocupar, liberar e cadastrar guichês."},
    {"name": "Usuários", "description": "Cadastro de atendentes e do gestor (somente GESTOR)."},
    {"name": "Relatórios", "description": "Relatórios diário e mensal e indicadores (somente GESTOR)."},
    {"name": "Fila e atendimento", "description": "Emissão, painel e chamadas (Dev A)."},
    {"name": "Saúde", "description": "Verificação do back end e do banco."},
]


def criar_app() -> FastAPI:
    config = get_config()
    configurar_logging()
    if config.expediente_forcar_aberto:
        logging.getLogger("nassau").warning("EXPEDIENTE_FORCAR_ABERTO=true: expediente ignorado (só para demonstração)")

    app = FastAPI(
        title="nassauTickets API",
        version="1.0.0",
        description=("Sistema de Controle de Atendimento de um Laboratório de Análises Clínicas.\n\n"
                     "Autenticação: faça `POST /api/v1/auth/login`, copie o `access_token` e use o botão "
                     "**Authorize**. Rotas públicas: `POST /senhas`, `GET /painel`, `GET /health`. "
                     "Todo erro segue o formato `{codigo, mensagem, detalhes, request_id}`."),
        openapi_tags=TAGS,
    )
    app.add_middleware(CORSMiddleware, allow_origins=config.cors_origens, allow_methods=["*"],
                       allow_headers=["*"], expose_headers=["X-Request-ID", "Retry-After"])
    app.middleware("http")(middleware_requisicao)
    registrar_handlers(app)

    for roteador in (saude, auth, cadastros, relatorios):
        app.include_router(roteador.router, prefix=PREFIXO)

    # Routers do Dev A: entram sozinhos quando o arquivo existir (cada um exporta `router`).
    for nome in ("senhas", "atendimento"):
        try:
            modulo = importlib.import_module(f"app.routers.{nome}")
        except ModuleNotFoundError as erro:
            if erro.name != f"app.routers.{nome}":
                raise
            continue
        app.include_router(modulo.router, prefix=PREFIXO)

    return app


app = criar_app()
