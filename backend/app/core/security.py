"""Senhas (argon2id), JWT e dependências de autorização (`usuario_atual`, `exigir_perfil`)."""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymysql.connections import Connection

from app.core.config import get_config
from app.core.db import get_conexao
from app.core.errors import ErroNegocio
from app.core.tempo import agora
from app.repositories import log_acesso as repo_log
from app.repositories import usuarios as repo_usuarios

logger = logging.getLogger("nassau.seguranca")
_hasher = PasswordHasher()  # argon2id com parâmetros padrão da biblioteca
_esquema_bearer = HTTPBearer(auto_error=False, description="Cole o `access_token` de POST /auth/login.")


@dataclass(frozen=True)
class UsuarioAtual:
    id: int
    nome: str
    perfil: str  # "ATENDENTE" ou "GESTOR"


# ---------- senhas ----------

def gerar_hash(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _hasher.verify(senha_hash, senha)
    except (VerificationError, InvalidHashError):
        return False


@lru_cache
def hash_falso() -> str:
    """Hash de uma senha qualquer; usado quando o e-mail não existe, para o tempo de resposta
    do login ser parecido nos dois casos (dificulta descobrir e-mails cadastrados)."""
    return gerar_hash("senha-que-ninguem-tem")


# ---------- JWT ----------

def criar_token(usuario_id: int, perfil: str) -> tuple[str, datetime]:
    config = get_config()
    agora_ = agora()
    expira_em = agora_ + timedelta(minutes=config.jwt_expira_min)
    carga = {"sub": str(usuario_id), "perfil": perfil, "iat": int(agora_.timestamp()), "exp": expira_em}
    return jwt.encode(carga, config.jwt_segredo, algorithm="HS256"), expira_em


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_config().jwt_segredo, algorithms=["HS256"],
                          options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        raise ErroNegocio("NAO_AUTENTICADO", "Token ausente, inválido ou expirado.", 401)


# ---------- dependências ----------

def usuario_atual(
    request: Request,
    credenciais: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
    conn: Connection = Depends(get_conexao),
) -> UsuarioAtual:
    """Identifica quem chamou. 401 se o token faltar, for inválido ou o usuário estiver inativo."""
    if credenciais is None:
        raise ErroNegocio("NAO_AUTENTICADO", "Token ausente, inválido ou expirado.", 401)
    carga = decodificar_token(credenciais.credentials)
    try:
        usuario_id = int(carga["sub"])
    except (TypeError, ValueError):
        raise ErroNegocio("NAO_AUTENTICADO", "Token ausente, inválido ou expirado.", 401)
    linha = repo_usuarios.buscar_por_id(conn, usuario_id)
    if linha is None or not linha["ativo"]:
        raise ErroNegocio("NAO_AUTENTICADO", "Token ausente, inválido ou expirado.", 401)
    usuario = UsuarioAtual(id=linha["id"], nome=linha["nome"], perfil=linha["perfil"])
    request.state.usuario = usuario
    return usuario


def _registrar_acesso(conn: Connection, request: Request, usuario_id: int, resultado: str) -> None:
    """Grava em log_acesso (LGPD). Uma falha aqui nunca derruba a requisição."""
    rota = request.scope.get("route")
    recurso = f"{request.method} {getattr(rota, 'path', request.url.path)}"
    ip = request.client.host if request.client else None
    try:
        repo_log.inserir(conn, usuario_id, "ACESSO", recurso, ip, resultado)
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("não foi possível gravar log_acesso")


def exigir_perfil(*perfis: str):
    """Fábrica de dependência. O GESTOR herda o perfil ATENDENTE (RN-13).

    Uso: `usuario: UsuarioAtual = Depends(exigir_perfil("GESTOR"))`.
    """
    permitidos = set(perfis)

    def dependencia(
        request: Request,
        usuario: UsuarioAtual = Depends(usuario_atual),
        conn: Connection = Depends(get_conexao),
    ) -> UsuarioAtual:
        efetivos = {usuario.perfil} | ({"ATENDENTE"} if usuario.perfil == "GESTOR" else set())
        if not permitidos & efetivos:
            _registrar_acesso(conn, request, usuario.id, "NEGADO")
            raise ErroNegocio("SEM_PERMISSAO", "Seu perfil não tem permissão para esta ação.", 403)
        _registrar_acesso(conn, request, usuario.id, "SUCESSO")
        return usuario

    return dependencia


usuario_logado = exigir_perfil("ATENDENTE", "GESTOR")
