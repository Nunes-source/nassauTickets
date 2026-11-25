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


def ativa_do_guiche(conn: Connection, guiche_id: int, dia) -> dict | None:
    """Senha do dia em CHAMADA, CHAMADA_NOVAMENTE ou EM_ATENDIMENTO cuja última chamada foi neste guichê.

    Mesma definição de "senha ativa" usada por `guiches.contar_senhas_ativas` (RN-12).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT s.id, s.numero, s.tipo, s.sequencia, s.estado, c.numero_chamada, c.chamada_em, "
            "c.guiche_id, g.numero AS guiche_numero "
            "FROM senhas s "
            "JOIN chamadas c ON c.senha_id = s.id "
            " AND c.numero_chamada = (SELECT MAX(numero_chamada) FROM chamadas WHERE senha_id = s.id) "
            "JOIN guiches g ON g.id = c.guiche_id "
            "WHERE c.guiche_id = %s AND s.data_emissao = %s "
            "AND s.estado IN ('CHAMADA', 'CHAMADA_NOVAMENTE', 'EM_ATENDIMENTO') "
            "ORDER BY c.chamada_em DESC LIMIT 1", (guiche_id, dia))
        return cur.fetchone()
