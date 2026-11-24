"""Cria o schema (se faltar) e os dados de DESENVOLVIMENTO: 3 usuários e 3 guichês.

Roda quantas vezes quiser: só insere o que ainda não existe. Uso: `python -m database.seed`
As credenciais abaixo são só de teste; nunca use este seed em produção.
"""
import os
import sys

from pymysql.connections import Connection

from app.core.db import conectar
from app.core.security import gerar_hash
from app.repositories import guiches as repo_guiches
from app.repositories import usuarios as repo_usuarios
from database import migrar

USUARIOS = [
    ("Gestor", "gestor@nassau.local", "Gestor@123", "GESTOR"),
    ("Atendente 1", "atendente1@nassau.local", "Atendente@123", "ATENDENTE"),
    ("Atendente 2", "atendente2@nassau.local", "Atendente@123", "ATENDENTE"),
]
GUICHES = (1, 2, 3)


def executar(conn: Connection) -> dict:
    resumo = {"migrations": migrar.aplicar(conn), "usuarios": 0, "guiches": 0}
    for nome, email, senha, perfil in USUARIOS:
        if repo_usuarios.buscar_por_email(conn, email) is None:
            repo_usuarios.inserir(conn, nome, email, gerar_hash(senha), perfil)
            resumo["usuarios"] += 1
    for numero in GUICHES:
        if not repo_guiches.numero_existe(conn, numero):
            repo_guiches.inserir(conn, numero)
            resumo["guiches"] += 1
    conn.commit()
    return resumo


if __name__ == "__main__":
    if os.getenv("AMBIENTE", "desenvolvimento").lower() == "producao":
        sys.exit("Seed recusado: AMBIENTE=producao.")
    conexao = conectar()
    try:
        resultado = executar(conexao)
    finally:
        conexao.close()
    print(f"Seed ok: {resultado['usuarios']} usuário(s) e {resultado['guiches']} guichê(s) criados; "
          f"migrations novas: {resultado['migrations'] or 'nenhuma'}.")
