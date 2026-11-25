"""SQL do health check."""
from pymysql.connections import Connection


def ping(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
