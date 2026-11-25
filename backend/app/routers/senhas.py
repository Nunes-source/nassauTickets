"""Emissão, painel e ações sobre uma senha (contrato §2 e §4)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pymysql.connections import Connection

from app.core.db import get_conexao
from app.core.security import UsuarioAtual, usuario_logado
from app.schemas.comum import respostas
from app.schemas.fila import ChamadaResposta, EmitirEntrada, IniciarResposta, PainelResposta, SenhaEmitida, SenhaResumo
from app.services import atendimento, emissao, fila

router = APIRouter()
TAG = ["Fila e atendimento"]
IdSenha = Annotated[int, Path(ge=1, description="Identificador da senha.")]


@router.post("/senhas", response_model=SenhaEmitida, status_code=201, tags=TAG, summary="Emitir senha (totem, público)",
             description="Gera o número `YYMMDD-PPSQ` e deixa a senha AGUARDANDO. Só dentro do expediente (07h–17h).",
             responses=respostas(409, 422, 503))
def emitir(corpo: EmitirEntrada, conn: Connection = Depends(get_conexao)):
    return emissao.emitir_senha(conn, corpo.tipo)


@router.get("/painel", response_model=PainelResposta, tags=TAG, summary="Painel: 5 últimas chamadas (público)",
            description="Mais recente primeiro. Nunca mostra a próxima senha. O front consulta a cada 2–3 s.",
            responses=respostas(503))
def painel(conn: Connection = Depends(get_conexao)):
    return fila.painel(conn)


@router.post("/senhas/{senha_id}/chamar-novamente", response_model=ChamadaResposta, tags=TAG,
             summary="Chamar novamente (2ª e última chamada)",
             description="Só de CHAMADA. Devolve `ultima_chamada: true`. Só quem chamou a senha (ou o gestor).",
             responses=respostas(401, 403, 404, 409, 503))
def chamar_novamente(senha_id: IdSenha, usuario: UsuarioAtual = Depends(usuario_logado),
                     conn: Connection = Depends(get_conexao)):
    return atendimento.chamar_novamente(conn, usuario, senha_id)


@router.post("/senhas/{senha_id}/iniciar-atendimento", response_model=IniciarResposta, tags=TAG,
             summary="Iniciar atendimento",
             description="De CHAMADA ou CHAMADA_NOVAMENTE para EM_ATENDIMENTO. Sorteia a duração simulada (RN-07).",
             responses=respostas(401, 403, 404, 409, 503))
def iniciar_atendimento(senha_id: IdSenha, usuario: UsuarioAtual = Depends(usuario_logado),
                        conn: Connection = Depends(get_conexao)):
    return atendimento.iniciar_atendimento(conn, usuario, senha_id)


@router.post("/senhas/{senha_id}/encerrar-atendimento", response_model=SenhaResumo, tags=TAG,
             summary="Encerrar atendimento",
             description="De EM_ATENDIMENTO para ATENDIDA. Permitido depois das 17h se já estava em curso.",
             responses=respostas(401, 403, 404, 409, 503))
def encerrar_atendimento(senha_id: IdSenha, usuario: UsuarioAtual = Depends(usuario_logado),
                         conn: Connection = Depends(get_conexao)):
    return atendimento.encerrar_atendimento(conn, usuario, senha_id)


@router.post("/senhas/{senha_id}/nao-compareceu", response_model=SenhaResumo, tags=TAG,
             summary="Registrar não comparecimento",
             description="Só depois da 2ª chamada (CHAMADA_NOVAMENTE). Motivo `ABANDONO`.",
             responses=respostas(401, 403, 404, 409, 503))
def nao_compareceu(senha_id: IdSenha, usuario: UsuarioAtual = Depends(usuario_logado),
                   conn: Connection = Depends(get_conexao)):
    return atendimento.registrar_nao_comparecimento(conn, usuario, senha_id)
