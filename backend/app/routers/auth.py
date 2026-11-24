"""Autenticação (contrato §3)."""
from fastapi import APIRouter, Depends, Request
from pymysql.connections import Connection

from app.core.db import get_conexao
from app.core.security import UsuarioAtual, usuario_logado
from app.schemas.auth import LoginEntrada, LoginResposta, UsuarioMe
from app.schemas.comum import respostas
from app.services import auth as servico

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=LoginResposta, summary="Entrar no sistema",
             description="Troca e-mail e senha por um token JWT (`Authorization: Bearer <token>`). "
                         "Qualquer falha responde o mesmo erro, sem dizer se o e-mail existe.",
             responses=respostas(401, 422, 503))
def login(corpo: LoginEntrada, request: Request, conn: Connection = Depends(get_conexao)):
    ip = request.client.host if request.client else None
    return servico.login(conn, corpo.email, corpo.senha, ip)


@router.get("/me", response_model=UsuarioMe, summary="Dados de quem está logado",
            description="Inclui o guichê que o atendente ocupa agora (ou `null`).",
            responses=respostas(401, 403, 503))
def me(usuario: UsuarioAtual = Depends(usuario_logado), conn: Connection = Depends(get_conexao)):
    return servico.dados_do_usuario(conn, usuario)
