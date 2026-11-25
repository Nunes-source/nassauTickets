"""SQL de `senhas`, `contadores_senha` e `senha_historico`."""
from datetime import date, datetime

from pymysql.connections import Connection

_COLUNAS = "id, numero, data_emissao, tipo, sequencia, estado, motivo_descarte, emitida_em"


# ---------------------------------------------------------------- emissão

def proximo_sequencial(conn: Connection, dia: date, tipo: str) -> int:
    """Próximo número do tipo no dia, atômico (docs/mer §5): a linha do contador fica travada até o commit."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO contadores_senha (data, tipo, ultimo_seq) VALUES (%s, %s, LAST_INSERT_ID(1)) "
            "ON DUPLICATE KEY UPDATE ultimo_seq = LAST_INSERT_ID(ultimo_seq + 1)", (dia, tipo))
        cur.execute("SELECT LAST_INSERT_ID() AS seq")
        return int(cur.fetchone()["seq"])


def inserir(conn: Connection, numero: str, dia: date, tipo: str, sequencia: int, estado: str,
            emitida_em: datetime) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO senhas (numero, data_emissao, tipo, sequencia, estado, emitida_em) "
            "VALUES (%s, %s, %s, %s, %s, %s)", (numero, dia, tipo, sequencia, estado, emitida_em))
        return cur.lastrowid


def atualizar_estado(conn: Connection, senha_id: int, estado: str, motivo: str | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE senhas SET estado = %s, motivo_descarte = %s WHERE id = %s", (estado, motivo, senha_id))


def registrar_historico(conn: Connection, senha_id: int, anterior: str | None, novo: str,
                        usuario_id: int | None, origem: str, quando: datetime) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO senha_historico (senha_id, estado_anterior, estado_novo, usuario_id, origem, ocorrido_em) "
            "VALUES (%s, %s, %s, %s, %s, %s)", (senha_id, anterior, novo, usuario_id, origem, quando))


# ----------------------------------------------------------------- leitura

def buscar_por_id(conn: Connection, senha_id: int, para_atualizar: bool = False) -> dict | None:
    sql = f"SELECT {_COLUNAS} FROM senhas WHERE id = %s"
    if para_atualizar:
        sql += " FOR UPDATE"
    with conn.cursor() as cur:
        cur.execute(sql, (senha_id,))
        return cur.fetchone()


def tipos_aguardando(conn: Connection, dia: date) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT tipo FROM senhas WHERE data_emissao = %s AND estado = 'AGUARDANDO'", (dia,))
        return [linha["tipo"] for linha in cur.fetchall()]


def proxima_aguardando(conn: Connection, dia: date, tipo: str) -> dict | None:
    """Menor sequência aguardando do tipo, já travada (FOR UPDATE)."""
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {_COLUNAS} FROM senhas WHERE data_emissao = %s AND estado = 'AGUARDANDO' AND tipo = %s "
            "ORDER BY sequencia LIMIT 1 FOR UPDATE", (dia, tipo))
        return cur.fetchone()


def contar_aguardando_por_tipo(conn: Connection, dia: date) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT tipo, COUNT(*) AS total FROM senhas WHERE data_emissao = %s AND estado = 'AGUARDANDO' "
                    "GROUP BY tipo", (dia,))
        return list(cur.fetchall())


def existe_aguardando(conn: Connection, dia: date) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 AS existe FROM senhas WHERE data_emissao = %s AND estado = 'AGUARDANDO' LIMIT 1", (dia,))
        return cur.fetchone() is not None


def listar_painel(conn: Connection, dia: date, limite: int) -> list[dict]:
    """Últimas senhas chamadas (cada senha aparece uma vez, com a chamada mais recente)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT s.numero, s.tipo, s.sequencia, g.numero AS guiche, c.numero_chamada, c.chamada_em "
            "FROM chamadas c JOIN senhas s ON s.id = c.senha_id JOIN guiches g ON g.id = c.guiche_id "
            "WHERE s.data_emissao = %s "
            "AND c.numero_chamada = (SELECT MAX(c2.numero_chamada) FROM chamadas c2 WHERE c2.senha_id = c.senha_id) "
            "ORDER BY c.chamada_em DESC, c.id DESC LIMIT %s", (dia, limite))
        return list(cur.fetchall())


# ------------------------------------------------------- descarte (RN-10)

def registrar_historico_descarte(conn: Connection, dia: date, quando: datetime) -> None:
    """Histórico do descarte em lote. Deve rodar ANTES de `descartar_aguardando` (lê o estado anterior)."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO senha_historico (senha_id, estado_anterior, estado_novo, usuario_id, origem, ocorrido_em) "
            "SELECT id, 'AGUARDANDO', 'NAO_COMPARECEU', NULL, 'SISTEMA', %s FROM senhas "
            "WHERE data_emissao = %s AND estado = 'AGUARDANDO'", (quando, dia))


def descartar_aguardando(conn: Connection, dia: date) -> int:
    with conn.cursor() as cur:
        cur.execute("UPDATE senhas SET estado = 'NAO_COMPARECEU', motivo_descarte = 'FIM_EXPEDIENTE' "
                    "WHERE data_emissao = %s AND estado = 'AGUARDANDO'", (dia,))
        return cur.rowcount
