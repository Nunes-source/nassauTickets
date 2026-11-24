"""Formato único de erro, request_id e ausência de detalhes técnicos (não precisa de banco)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import ErroNegocio, registrar_handlers
from app.core.logging import middleware_requisicao


class Corpo(BaseModel):
    quantidade: int


@pytest.fixture
def cliente():
    app = FastAPI()
    registrar_handlers(app)
    app.middleware("http")(middleware_requisicao)

    @app.get("/negocio")
    def negocio():
        raise ErroNegocio("TRANSICAO_INVALIDA", "Não pode.", 409, {"de": "AGUARDANDO"})

    @app.get("/quebra")
    def quebra():
        raise RuntimeError("senha-do-banco-vazada")

    @app.post("/valida")
    def valida(corpo: Corpo):
        return corpo

    return TestClient(app, raise_server_exceptions=False)


def test_erro_de_negocio_segue_o_formato_padrao(cliente):
    resposta = cliente.get("/negocio")
    corpo = resposta.json()
    assert resposta.status_code == 409
    assert set(corpo) == {"codigo", "mensagem", "detalhes", "request_id"}
    assert corpo["codigo"] == "TRANSICAO_INVALIDA" and corpo["detalhes"] == {"de": "AGUARDANDO"}
    assert corpo["request_id"] == resposta.headers["X-Request-ID"]


def test_erro_inesperado_vira_500_generico_sem_detalhes_tecnicos(cliente):
    resposta = cliente.get("/quebra")
    assert resposta.status_code == 500
    assert resposta.json()["codigo"] == "ERRO_INTERNO"
    assert "senha-do-banco-vazada" not in resposta.text and "Traceback" not in resposta.text
    assert resposta.headers["X-Request-ID"]


def test_validacao_lista_os_campos(cliente):
    resposta = cliente.post("/valida", json={"quantidade": "abc"})
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["codigo"] == "VALIDACAO"
    assert corpo["detalhes"]["campos"][0]["campo"] == "quantidade"


def test_rota_inexistente_vira_nao_encontrado_padronizado(cliente):
    resposta = cliente.get("/nao-existe")
    assert resposta.status_code == 404
    assert resposta.json()["codigo"] == "NAO_ENCONTRADO"
