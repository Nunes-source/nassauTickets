"""SQL da tabela `log_acesso` (LGPD). Nunca grava senha nem token."""
from pymysql.connections import Connection


def inserir(conn: Connection, usuario_id: int | None, acao: str, recurso: str | None,
            ip: str | None, resultado: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO log_acesso (usuario_id, acao, recurso, ip, resultado) VALUES (%s, %s, %s, %s, %s)",
            (usuario_id, acao[:60], recurso[:150] if recurso else None, ip[:45] if ip else None, resultado),
        )
