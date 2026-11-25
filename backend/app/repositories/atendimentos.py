"""SQL de `atendimentos`."""
from datetime import datetime

from pymysql.connections import Connection


def inserir(conn: Connection, senha_id: int, guiche_id: int, usuario_id: int, iniciado_em: datetime,
            duracao_simulada_seg: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO atendimentos (senha_id, guiche_id, usuario_id, iniciado_em, duracao_simulada_seg) "
            "VALUES (%s, %s, %s, %s, %s)", (senha_id, guiche_id, usuario_id, iniciado_em, duracao_simulada_seg))


def finalizar(conn: Connection, senha_id: int, quando: datetime) -> int:
    with conn.cursor() as cur:
        cur.execute("UPDATE atendimentos SET finalizado_em = %s WHERE senha_id = %s AND finalizado_em IS NULL",
                    (quando, senha_id))
        return cur.rowcount
