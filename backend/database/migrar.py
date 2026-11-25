"""Aplica os arquivos `schema/*.sql` em ordem alfabética, uma única vez cada (migrations simples).

Uso: `python -m database.migrar`
"""
import re
from pathlib import Path

from pymysql.connections import Connection

from app.core.db import conectar

PASTA_SCHEMA = Path(__file__).parent / "schema"


def dividir_sql(texto: str) -> list[str]:
    """Remove comentários `-- ...` e separa os comandos por `;` (os schemas não têm procedures)."""
    sem_comentarios = re.sub(r"--[^\n]*", "", texto)
    return [c.strip() for c in sem_comentarios.split(";") if c.strip()]


def aplicar(conn: Connection, pasta: Path = PASTA_SCHEMA) -> list[str]:
    """Devolve os arquivos aplicados agora. É seguro rodar várias vezes."""
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migracoes ("
            " arquivo VARCHAR(100) NOT NULL PRIMARY KEY,"
            " aplicado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4")
        cur.execute("SELECT arquivo FROM schema_migracoes")
        ja_aplicados = {linha["arquivo"] for linha in cur.fetchall()}
    novos = []
    for arquivo in sorted(pasta.glob("*.sql")):
        if arquivo.name in ja_aplicados:
            continue
        with conn.cursor() as cur:
            for comando in dividir_sql(arquivo.read_text(encoding="utf-8")):
                cur.execute(comando)
            cur.execute("INSERT INTO schema_migracoes (arquivo) VALUES (%s)", (arquivo.name,))
        conn.commit()
        novos.append(arquivo.name)
    return novos


def apagar_tudo(conn: Connection) -> None:
    """Remove todas as tabelas. SÓ para o banco de testes."""
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute("SHOW TABLES")
        for linha in cur.fetchall():
            cur.execute(f"DROP TABLE IF EXISTS `{next(iter(linha.values()))}`")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()


if __name__ == "__main__":
    conexao = conectar()
    try:
        aplicados = aplicar(conexao)
    finally:
        conexao.close()
    print("Migrations aplicadas:", ", ".join(aplicados) if aplicados else "nenhuma (já estava em dia)")
