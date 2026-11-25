"""SQL de `fila_estado`: a linha do dia é o "cadeado" do chamar próximo (ADR-002)."""
from datetime import date

from pymysql.connections import Connection


def garantir_linha(conn: Connection, dia: date) -> None:
    with conn.cursor() as cur:
        cur.execute("INSERT IGNORE INTO fila_estado (data) VALUES (%s)", (dia,))


def travar_e_ler(conn: Connection, dia: date) -> str | None:
    """Trava a linha do dia (as outras chamadas esperam aqui) e devolve o último tipo chamado."""
    with conn.cursor() as cur:
        cur.execute("SELECT ultimo_tipo FROM fila_estado WHERE data = %s FOR UPDATE", (dia,))
        return cur.fetchone()["ultimo_tipo"]


def definir_ultimo_tipo(conn: Connection, dia: date, tipo: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE fila_estado SET ultimo_tipo = %s WHERE data = %s", (tipo, dia))
