"""Chamar próximo e resumo da fila (contrato §4)."""
from fastapi import APIRouter, Depends
from pymysql.connections import Connection

from app.core.db import get_conexao
from app.core.security import UsuarioAtual, usuario_logado
from app.schemas.comum import respostas
from app.schemas.fila import ChamadaResposta
from app.services import atendimento, fila

router = APIRouter()
TAG = ["Fila e atendimento"]


@router.post("/atendimentos/chamar-proximo", response_model=ChamadaResposta, tags=TAG,
             summary="Chamar a próxima senha",
             description=("Escolhe a próxima senha (prioridade SP > SE > SG, nunca repetindo o tipo anterior se houver "
                          "outro) com lock na fila (ADR-002/003). Exige um guichê ocupado e livre de senha ativa."),
             responses=respostas(401, 403, 404, 409, 503))
def chamar_proximo(usuario: UsuarioAtual = Depends(usuario_logado), conn: Connection = Depends(get_conexao)):
    return atendimento.chamar_proximo(conn, usuario)


@router.get("/fila/resumo", response_model=dict[str, int], tags=TAG, summary="Quantas senhas aguardam, por tipo",
            responses={**respostas(401, 403, 503),
                       200: {"content": {"application/json": {"example": {"SP": 2, "SE": 0, "SG": 5}}}}})
def resumo_da_fila(_: UsuarioAtual = Depends(usuario_logado), conn: Connection = Depends(get_conexao)):
    return fila.resumo(conn)
