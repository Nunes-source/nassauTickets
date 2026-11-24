"""Conexão com o MySQL (PyMySQL, SQL direto) com retry e transação explícita."""
import time
from contextlib import contextmanager
from typing import Iterator

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from app.core.config import get_config
from app.core.errors import ErroNegocio

# 1 tentativa + 3 novas tentativas, esperando 0,2 s / 0,5 s / 1 s (docs/requirements/02 §3)
ESPERAS_RETRY = (0.2, 0.5, 1.0)


def _conectar_uma_vez() -> Connection:
    config = get_config()
    return pymysql.connect(
        host=config.db_host,
        port=config.db_porta,
        user=config.db_usuario,
        password=config.db_senha,
        database=config.db_nome,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=3,
    )


def conectar(esperas: tuple[float, ...] = ESPERAS_RETRY) -> Connection:
    """Abre uma conexão. Se o banco estiver fora, tenta de novo e por fim levanta 503."""
    for espera in (*esperas, None):
        try:
            return _conectar_uma_vez()
        except (pymysql.err.OperationalError, pymysql.err.InterfaceError):
            if espera is None:
                raise ErroNegocio("BANCO_INDISPONIVEL",
                                  "Banco de dados indisponível. Tente novamente em instantes.", 503)
            time.sleep(espera)
    raise AssertionError("inalcançável")  # pragma: no cover


def get_conexao() -> Iterator[Connection]:
    """Dependência do FastAPI: uma conexão por requisição, sempre fechada no final."""
    conn = conectar()
    try:
        yield conn
    finally:
        try:
            conn.rollback()  # descarta qualquer transação que ficou aberta
        finally:
            conn.close()


@contextmanager
def transacao(conn: Connection) -> Iterator[Connection]:
    """Commit se o bloco termina bem; rollback se qualquer exceção sair dele."""
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
