"""Configuração dos testes.

- Testes sem banco (tempo, períodos, erros, retry): rodam em qualquer máquina.
- Testes com banco: usam o MySQL de teste (`DB_NAME_TEST`, padrão `<DB_NAME>_test`) e são PULADOS se ele não responder.
  Com Docker Compose: `docker compose --env-file backend/.env up -d db` e depois `cd backend && pytest`.
"""
import os

from dotenv import load_dotenv

load_dotenv()  # lê backend/.env (se existir) ANTES de fixarmos o que os testes exigem
os.environ.setdefault("JWT_SECRET", "segredo-de-teste-com-mais-de-16-caracteres")
os.environ["EXPEDIENTE_INICIO"] = "07:00"
os.environ["EXPEDIENTE_FIM"] = "17:00"
os.environ["DB_NAME"] = os.getenv("DB_NAME_TEST") or f"{os.getenv('DB_NAME', 'nassau_tickets')}_test"

import pytest  # noqa: E402

API = "/api/v1"


@pytest.fixture(scope="session")
def banco():
    """Conexão com o MySQL de teste, com o schema recriado do zero. Pula se não houver banco."""
    from app.core.db import conectar
    from app.core.errors import ErroNegocio
    from database import migrar

    try:
        conn = conectar(esperas=())
    except ErroNegocio:
        pytest.skip("MySQL de teste indisponível")
    migrar.apagar_tudo(conn)
    migrar.aplicar(conn)
    yield conn
    conn.close()


@pytest.fixture
def ambiente(banco):
    """Banco limpo + seed (3 usuários, 3 guichês) para cada teste."""
    from database import seed

    with banco.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute("SHOW TABLES")
        for linha in cur.fetchall():
            tabela = next(iter(linha.values()))
            if tabela != "schema_migracoes":
                cur.execute(f"TRUNCATE TABLE `{tabela}`")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    banco.commit()
    seed.executar(banco)
    return banco


@pytest.fixture
def cliente(ambiente):
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def _entrar(cliente, email: str, senha: str) -> dict:
    resposta = cliente.post(f"{API}/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


@pytest.fixture
def gestor(cliente):
    return _entrar(cliente, "gestor@nassau.local", "Gestor@123")


@pytest.fixture
def atendente1(cliente):
    return _entrar(cliente, "atendente1@nassau.local", "Atendente@123")


@pytest.fixture
def atendente2(cliente):
    return _entrar(cliente, "atendente2@nassau.local", "Atendente@123")


def consultar(banco, sql: str, params: tuple = ()) -> list[dict]:
    """Atalho para conferir o que ficou gravado no banco."""
    banco.commit()  # enxerga o que a API acabou de gravar
    with banco.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())
