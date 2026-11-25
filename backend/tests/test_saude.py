"""Health check, retry de conexão e comportamento com o banco fora do ar (RNF-05)."""
import pytest

from app.core import db
from app.core.errors import ErroNegocio
from tests.conftest import API


def _derrubar_banco(monkeypatch):
    def falha(*args, **kwargs):
        raise ErroNegocio("BANCO_INDISPONIVEL", "Banco de dados indisponível. Tente novamente em instantes.", 503)

    monkeypatch.setattr("app.core.db.conectar", falha)
    monkeypatch.setattr("app.routers.saude.conectar", falha)


def test_health_ok(cliente):
    resposta = cliente.get(f"{API}/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_health_com_banco_fora_responde_503(cliente, monkeypatch):
    _derrubar_banco(monkeypatch)
    resposta = cliente.get(f"{API}/health")
    assert resposta.status_code == 503
    assert resposta.json() == {"status": "degradado", "banco": "falha"}
    assert resposta.headers["Retry-After"] == "5"


def test_rota_protegida_com_banco_fora_responde_503_padronizado(cliente, monkeypatch):
    _derrubar_banco(monkeypatch)
    resposta = cliente.get(f"{API}/auth/me", headers={"Authorization": "Bearer qualquer"})
    corpo = resposta.json()
    assert resposta.status_code == 503
    assert corpo["codigo"] == "BANCO_INDISPONIVEL"
    assert corpo["request_id"] and "Traceback" not in resposta.text
    assert resposta.headers["Retry-After"] == "5"


def test_banco_volta_e_o_sistema_se_recupera(cliente, monkeypatch):
    with monkeypatch.context() as m:
        _derrubar_banco(m)
        assert cliente.get(f"{API}/health").status_code == 503
    assert cliente.get(f"{API}/health").status_code == 200  # sem reiniciar nada


# ---- retry de conexão (não precisa de banco) ----

def test_conectar_tenta_de_novo_e_espera_0_2_e_0_5(monkeypatch):
    import pymysql

    esperas, tentativas = [], []

    def instavel():
        tentativas.append(1)
        if len(tentativas) < 3:
            raise pymysql.err.OperationalError(2003, "sem conexão")
        return "conexao"

    monkeypatch.setattr(db, "_conectar_uma_vez", instavel)
    monkeypatch.setattr(db.time, "sleep", esperas.append)
    assert db.conectar() == "conexao"
    assert len(tentativas) == 3
    assert esperas == [0.2, 0.5]


def test_conectar_desiste_depois_de_1_mais_3_tentativas(monkeypatch):
    import pymysql

    esperas, tentativas = [], []

    def fora():
        tentativas.append(1)
        raise pymysql.err.OperationalError(2003, "sem conexão")

    monkeypatch.setattr(db, "_conectar_uma_vez", fora)
    monkeypatch.setattr(db.time, "sleep", esperas.append)
    with pytest.raises(ErroNegocio) as erro:
        db.conectar()
    assert erro.value.codigo == "BANCO_INDISPONIVEL" and erro.value.status == 503
    assert len(tentativas) == 4
    assert esperas == [0.2, 0.5, 1.0]
