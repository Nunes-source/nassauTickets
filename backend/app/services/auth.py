"""Login e dados do usuário logado."""
from pymysql.connections import Connection

from app.core.errors import ErroNegocio
from app.core.security import UsuarioAtual, criar_token, hash_falso, verificar_senha
from app.repositories import guiches as repo_guiches
from app.repositories import log_acesso as repo_log
from app.repositories import usuarios as repo_usuarios


def _registrar(conn: Connection, usuario_id: int | None, ip: str | None, resultado: str) -> None:
    repo_log.inserir(conn, usuario_id, "LOGIN", "POST /auth/login", ip, resultado)
    conn.commit()  # precisa persistir mesmo quando a seguir levantamos erro


def login(conn: Connection, email: str, senha: str, ip: str | None) -> dict:
    usuario = repo_usuarios.buscar_por_email(conn, email.strip().lower())
    # Sempre confere um hash, exista o e-mail ou não (tempo de resposta parecido).
    senha_ok = verificar_senha(senha, usuario["senha_hash"] if usuario else hash_falso())
    if usuario is None or not senha_ok or not usuario["ativo"]:
        _registrar(conn, usuario["id"] if usuario else None, ip, "FALHA")
        raise ErroNegocio("CREDENCIAIS_INVALIDAS", "E-mail ou senha inválidos.", 401)
    token, expira_em = criar_token(usuario["id"], usuario["perfil"])
    _registrar(conn, usuario["id"], ip, "SUCESSO")
    return {"access_token": token, "token_type": "bearer", "expira_em": expira_em,
            "perfil": usuario["perfil"], "nome": usuario["nome"]}


def dados_do_usuario(conn: Connection, atual: UsuarioAtual) -> dict:
    usuario = repo_usuarios.buscar_por_id(conn, atual.id)
    guiche = repo_guiches.buscar_por_usuario(conn, atual.id)
    return {
        "id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"], "perfil": usuario["perfil"],
        "guiche": {"id": guiche["id"], "numero": guiche["numero"]} if guiche else None,
    }
