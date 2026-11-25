"""SQL de `chamadas`."""
from datetime import datetime

from pymysql.connections import Connection


def inserir(conn: Connection, senha_id: int, guiche_id: int, usuario_id: int, numero_chamada: int,
            quando: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chamadas (senha_id, guiche_id, usuario_id, numero_chamada, chamada_em) "
            "VALUES (%s, %s, %s, %s, %s)", (senha_id, guiche_id, usuario_id, numero_chamada, quando))


def ultima_da_senha(conn: Connection, senha_id: int) -> dict | None:
    """Chamada mais recente da senha, com o número do guichê."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT c.numero_chamada, c.chamada_em, c.usuario_id, c.guiche_id, g.numero AS guiche_numero "
            "FROM chamadas c JOIN guiches g ON g.id = c.guiche_id WHERE c.senha_id = %s "
            "ORDER BY c.numero_chamada DESC LIMIT 1", (senha_id,))
        return cur.fetchone()
