"""SQL da tabela `guiches` (e a leitura de senhas ativas, que pertencem ao Dev A)."""
from datetime import date

import pymysql
from pymysql.connections import Connection

_BASE = (
    "SELECT g.id, g.numero, g.ativo, g.usuario_id, u.nome AS ocupante_nome "
    "FROM guiches g LEFT JOIN usuarios u ON u.id = g.usuario_id"
)


def listar(conn: Connection, apenas_livres: bool = False) -> list[dict]:
    sql = _BASE
    if apenas_livres:
        sql += " WHERE g.ativo = 1 AND g.usuario_id IS NULL"
    with conn.cursor() as cur:
        cur.execute(sql + " ORDER BY g.numero")
        return list(cur.fetchall())


def buscar_por_id(conn: Connection, guiche_id: int, para_atualizar: bool = False) -> dict | None:
    sql = _BASE + " WHERE g.id = %s"
    if para_atualizar:
        sql += " FOR UPDATE"
    with conn.cursor() as cur:
        cur.execute(sql, (guiche_id,))
        return cur.fetchone()


def buscar_por_usuario(conn: Connection, usuario_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(_BASE + " WHERE g.usuario_id = %s", (usuario_id,))
        return cur.fetchone()


def numero_existe(conn: Connection, numero: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM guiches WHERE numero = %s", (numero,))
        return cur.fetchone() is not None


def inserir(conn: Connection, numero: int) -> int:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO guiches (numero) VALUES (%s)", (numero,))
        return cur.lastrowid


def definir_ativo(conn: Connection, guiche_id: int, ativo: bool) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE guiches SET ativo = %s WHERE id = %s", (1 if ativo else 0, guiche_id))


def definir_ocupante(conn: Connection, guiche_id: int, usuario_id: int | None) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE guiches SET usuario_id = %s WHERE id = %s", (usuario_id, guiche_id))


def contar_senhas_ativas(conn: Connection, guiche_id: int, dia: date) -> int:
    """Senhas do dia em CHAMADA, CHAMADA_NOVAMENTE ou EM_ATENDIMENTO cuja última chamada foi neste guichê.

    Só leitura em tabelas do Dev A (`senhas`, `chamadas`). Se o schema da fila ainda não foi
    aplicado (erro 1146), não há senha ativa possível.
    """
    sql = (
        "SELECT COUNT(*) AS total FROM senhas s "
        "JOIN chamadas c ON c.senha_id = s.id "
        " AND c.numero_chamada = (SELECT MAX(numero_chamada) FROM chamadas WHERE senha_id = s.id) "
        "WHERE c.guiche_id = %s AND s.data_emissao = %s "
        "AND s.estado IN ('CHAMADA', 'CHAMADA_NOVAMENTE', 'EM_ATENDIMENTO')"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (guiche_id, dia))
            return int(cur.fetchone()["total"])
    except pymysql.err.ProgrammingError as erro:
        if erro.args and erro.args[0] == 1146:
            return 0
        raise
