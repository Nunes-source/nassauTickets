"""Consultas de relatórios e indicadores. Só leitura, em tabelas do Dev A e do Dev B."""
from datetime import date

from pymysql.connections import Connection


def _todas(conn: Connection, sql: str, params: tuple) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def resumo_por_tipo(conn: Connection, de: date, ate: date) -> list[dict]:
    return _todas(conn, (
        "SELECT tipo, COUNT(*) AS emitidas, "
        "SUM(estado = 'ATENDIDA') AS atendidas, SUM(estado = 'NAO_COMPARECEU') AS nao_compareceu "
        "FROM senhas WHERE data_emissao BETWEEN %s AND %s GROUP BY tipo"
    ), (de, ate))


def contar_senhas(conn: Connection, de: date, ate: date) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM senhas WHERE data_emissao BETWEEN %s AND %s", (de, ate))
        return int(cur.fetchone()["total"])


def listar_senhas(conn: Connection, de: date, ate: date, limite: int, deslocamento: int) -> list[dict]:
    return _todas(conn, (
        "SELECT s.numero, s.tipo, s.emitida_em, a.iniciado_em AS atendimento_inicio, "
        "a.finalizado_em AS atendimento_fim, g.numero AS guiche "
        "FROM senhas s "
        "LEFT JOIN atendimentos a ON a.senha_id = s.id "
        "LEFT JOIN guiches g ON g.id = a.guiche_id "
        "WHERE s.data_emissao BETWEEN %s AND %s "
        "ORDER BY s.emitida_em, s.id LIMIT %s OFFSET %s"
    ), (de, ate, limite, deslocamento))


def tm_por_tipo(conn: Connection, de: date, ate: date) -> list[dict]:
    return _todas(conn, (
        "SELECT s.tipo, COUNT(*) AS quantidade, AVG(a.duracao_simulada_seg) AS tm_simulado_medio_seg, "
        "AVG(CASE WHEN a.finalizado_em IS NOT NULL "
        "    THEN TIMESTAMPDIFF(SECOND, a.iniciado_em, a.finalizado_em) END) AS tm_real_medio_seg "
        "FROM atendimentos a JOIN senhas s ON s.id = a.senha_id "
        "WHERE s.data_emissao BETWEEN %s AND %s GROUP BY s.tipo"
    ), (de, ate))


def contar_auditoria(conn: Connection, de: date, ate: date) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS total FROM senhas s JOIN chamadas c ON c.senha_id = s.id "
            "AND c.numero_chamada = 1 WHERE s.data_emissao BETWEEN %s AND %s", (de, ate))
        return int(cur.fetchone()["total"])


def listar_auditoria(conn: Connection, de: date, ate: date, limite: int, deslocamento: int) -> list[dict]:
    """Uma linha por senha chamada (inclui NAO_COMPARECEU, sem início e fim de atendimento)."""
    return _todas(conn, (
        "SELECT u.nome AS atendente, g.numero AS guiche, s.numero AS senha, "
        "c1.chamada_em AS primeira_chamada_em, c2.chamada_em AS segunda_chamada_em, "
        "a.iniciado_em AS inicio_atendimento_em, a.finalizado_em AS fim_atendimento_em "
        "FROM senhas s "
        "JOIN chamadas c1 ON c1.senha_id = s.id AND c1.numero_chamada = 1 "
        "LEFT JOIN chamadas c2 ON c2.senha_id = s.id AND c2.numero_chamada = 2 "
        "JOIN usuarios u ON u.id = c1.usuario_id "
        "JOIN guiches g ON g.id = c1.guiche_id "
        "LEFT JOIN atendimentos a ON a.senha_id = s.id "
        "WHERE s.data_emissao BETWEEN %s AND %s "
        "ORDER BY c1.chamada_em, s.id LIMIT %s OFFSET %s"
    ), (de, ate, limite, deslocamento))


# ---- indicadores (RF-16) ----

def espera_media_por_tipo(conn: Connection, de: date, ate: date) -> list[dict]:
    return _todas(conn, (
        "SELECT s.tipo, AVG(TIMESTAMPDIFF(SECOND, s.emitida_em, c.chamada_em)) AS media_seg "
        "FROM senhas s JOIN chamadas c ON c.senha_id = s.id AND c.numero_chamada = 1 "
        "WHERE s.data_emissao BETWEEN %s AND %s GROUP BY s.tipo"
    ), (de, ate))


def atendimento_medio_por_tipo(conn: Connection, de: date, ate: date) -> list[dict]:
    return _todas(conn, (
        "SELECT s.tipo, AVG(TIMESTAMPDIFF(SECOND, a.iniciado_em, a.finalizado_em)) AS media_seg "
        "FROM atendimentos a JOIN senhas s ON s.id = a.senha_id "
        "WHERE s.data_emissao BETWEEN %s AND %s AND a.finalizado_em IS NOT NULL GROUP BY s.tipo"
    ), (de, ate))


def contagem_nao_comparecimento(conn: Connection, de: date, ate: date) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS emitidas, "
            "COALESCE(SUM(estado = 'NAO_COMPARECEU' AND motivo_descarte = 'ABANDONO'), 0) AS abandonadas "
            "FROM senhas WHERE data_emissao BETWEEN %s AND %s", (de, ate))
        return cur.fetchone()


def atendimentos_por_guiche(conn: Connection, de: date, ate: date) -> list[dict]:
    return _todas(conn, (
        "SELECT g.numero AS guiche, COUNT(*) AS quantidade "
        "FROM atendimentos a JOIN senhas s ON s.id = a.senha_id JOIN guiches g ON g.id = a.guiche_id "
        "WHERE s.data_emissao BETWEEN %s AND %s AND s.estado = 'ATENDIDA' "
        "GROUP BY g.numero ORDER BY g.numero"
    ), (de, ate))


def atendimentos_por_atendente(conn: Connection, de: date, ate: date) -> list[dict]:
    return _todas(conn, (
        "SELECT u.nome AS atendente, COUNT(*) AS quantidade "
        "FROM atendimentos a JOIN senhas s ON s.id = a.senha_id JOIN usuarios u ON u.id = a.usuario_id "
        "WHERE s.data_emissao BETWEEN %s AND %s AND s.estado = 'ATENDIDA' "
        "GROUP BY u.id, u.nome ORDER BY u.nome"
    ), (de, ate))


def total_atendidas(conn: Connection, de: date, ate: date) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM senhas WHERE data_emissao BETWEEN %s AND %s "
                    "AND estado = 'ATENDIDA'", (de, ate))
        return int(cur.fetchone()["total"])
