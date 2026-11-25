"""SQL de `fila_estado`: a linha do dia é o "cadeado" do chamar próximo (ADR-002)."""
from datetime import date

from pymysql.connections import Connection


def garantir_linha(conn: Connection, dia: date) -> None:
    """Cria a linha do dia se não existir, já pegando o lock EXCLUSIVO dela.

    Não usar `INSERT IGNORE` aqui: com a linha já existente ele pega um lock COMPARTILHADO, e o
    `SELECT ... FOR UPDATE` seguinte tenta promovê-lo a exclusivo. Com vários guichês ao mesmo
    tempo, cada um segura o compartilhado esperando os outros soltarem: deadlock (erro 1213).
    `ON DUPLICATE KEY UPDATE` pega o lock exclusivo direto; as chamadas só entram em fila.
    """
    with conn.cursor() as cur:
        cur.execute("INSERT INTO fila_estado (data) VALUES (%s) ON DUPLICATE KEY UPDATE data = data", (dia,))


def travar_e_ler(conn: Connection, dia: date) -> str | None:
    """Trava a linha do dia (as outras chamadas esperam aqui) e devolve o último tipo chamado."""
    with conn.cursor() as cur:
        cur.execute("SELECT ultimo_tipo FROM fila_estado WHERE data = %s FOR UPDATE", (dia,))
        return cur.fetchone()["ultimo_tipo"]


def definir_ultimo_tipo(conn: Connection, dia: date, tipo: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE fila_estado SET ultimo_tipo = %s WHERE data = %s", (tipo, dia))
