"""SQL da tabela `usuarios`."""
from pymysql.connections import Connection

_COLUNAS = "id, nome, email, senha_hash, perfil, ativo"
# Colunas que o PATCH pode alterar. Os NOMES vêm desta lista fixa (nunca do cliente);
# os VALORES sempre vão como parâmetros (%s).
COLUNAS_EDITAVEIS = ("nome", "email", "senha_hash", "perfil", "ativo")


def buscar_por_email(conn: Connection, email: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(f"SELECT {_COLUNAS} FROM usuarios WHERE email = %s", (email,))
        return cur.fetchone()


def buscar_por_id(conn: Connection, usuario_id: int, para_atualizar: bool = False) -> dict | None:
    sql = f"SELECT {_COLUNAS} FROM usuarios WHERE id = %s"
    if para_atualizar:
        sql += " FOR UPDATE"
    with conn.cursor() as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchone()


def listar(conn: Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, nome, email, perfil, ativo FROM usuarios ORDER BY nome, id")
        return list(cur.fetchall())


def inserir(conn: Connection, nome: str, email: str, senha_hash: str, perfil: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (%s, %s, %s, %s)",
            (nome, email, senha_hash, perfil),
        )
        return cur.lastrowid


def atualizar(conn: Connection, usuario_id: int, campos: dict) -> None:
    colunas = [c for c in COLUNAS_EDITAVEIS if c in campos]
    if not colunas:
        return
    atribuicoes = ", ".join(f"{c} = %s" for c in colunas)
    valores = [campos[c] for c in colunas]
    with conn.cursor() as cur:
        cur.execute(f"UPDATE usuarios SET {atribuicoes} WHERE id = %s", (*valores, usuario_id))


def email_em_uso(conn: Connection, email: str, excluir_id: int | None = None) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s AND id <> %s", (email, excluir_id or 0))
        return cur.fetchone() is not None


def existe_gestor_ativo(conn: Connection, excluir_id: int | None = None) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM usuarios WHERE perfil = 'GESTOR' AND ativo = 1 AND id <> %s",
            (excluir_id or 0,),
        )
        return cur.fetchone() is not None
