"""Usuários e guichês (contrato §4 e §5)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from pymysql.connections import Connection

from app.core.db import get_conexao
from app.core.security import UsuarioAtual, exigir_perfil, usuario_logado
from app.schemas.comum import respostas
from app.schemas.guiches import GuicheAtualizar, GuicheCriar, GuicheSaida
from app.schemas.usuarios import UsuarioAtualizar, UsuarioCriar, UsuarioSaida
from app.services import cadastros as servico

router = APIRouter()
somente_gestor = exigir_perfil("GESTOR")
IdRecurso = Annotated[int, Path(ge=1, description="Identificador do recurso.")]


# ------------------------------------------------------------------ guichês

@router.get("/guiches", response_model=list[GuicheSaida], tags=["Guichês"], summary="Listar guichês",
            description="`livres=true` devolve só os guichês ativos e sem atendente.",
            responses=respostas(401, 403, 503))
def listar_guiches(livres: bool = Query(False, description="Só guichês livres."),
                   _: UsuarioAtual = Depends(usuario_logado), conn: Connection = Depends(get_conexao)):
    return servico.listar_guiches(conn, livres)


@router.post("/guiches/{guiche_id}/ocupar", response_model=GuicheSaida, tags=["Guichês"],
             summary="Ocupar um guichê",
             description="O atendente assume o guichê. Repetir a chamada no próprio guichê é inofensivo.",
             responses=respostas(401, 403, 404, 409, 503))
def ocupar_guiche(guiche_id: IdRecurso, usuario: UsuarioAtual = Depends(usuario_logado),
                  conn: Connection = Depends(get_conexao)):
    return servico.ocupar_guiche(conn, guiche_id, usuario)


@router.post("/guiches/{guiche_id}/liberar", response_model=GuicheSaida, tags=["Guichês"],
             summary="Liberar um guichê",
             description="Só o ocupante (ou o gestor) libera, e só sem senha ativa no guichê.",
             responses=respostas(401, 403, 404, 409, 503))
def liberar_guiche(guiche_id: IdRecurso, usuario: UsuarioAtual = Depends(usuario_logado),
                   conn: Connection = Depends(get_conexao)):
    return servico.liberar_guiche(conn, guiche_id, usuario)


@router.post("/guiches", response_model=GuicheSaida, status_code=201, tags=["Guichês"],
             summary="Cadastrar guichê (gestor)", responses=respostas(401, 403, 409, 422, 503))
def criar_guiche(corpo: GuicheCriar, _: UsuarioAtual = Depends(somente_gestor),
                 conn: Connection = Depends(get_conexao)):
    return servico.criar_guiche(conn, corpo.numero)


@router.patch("/guiches/{guiche_id}", response_model=GuicheSaida, tags=["Guichês"],
              summary="Ativar ou desativar guichê (gestor)",
              responses=respostas(401, 403, 404, 409, 422, 503))
def atualizar_guiche(corpo: GuicheAtualizar, guiche_id: IdRecurso,
                     _: UsuarioAtual = Depends(somente_gestor), conn: Connection = Depends(get_conexao)):
    return servico.atualizar_guiche(conn, guiche_id, corpo.ativo)


# ----------------------------------------------------------------- usuários

@router.get("/usuarios", response_model=list[UsuarioSaida], tags=["Usuários"],
            summary="Listar usuários (gestor)", responses=respostas(401, 403, 503))
def listar_usuarios(_: UsuarioAtual = Depends(somente_gestor), conn: Connection = Depends(get_conexao)):
    return servico.listar_usuarios(conn)


@router.post("/usuarios", response_model=UsuarioSaida, status_code=201, tags=["Usuários"],
             summary="Cadastrar usuário (gestor)",
             description="Só pode existir um GESTOR ativo (`GESTOR_JA_EXISTE`). O e-mail é único.",
             responses=respostas(401, 403, 409, 422, 503))
def criar_usuario(corpo: UsuarioCriar, _: UsuarioAtual = Depends(somente_gestor),
                  conn: Connection = Depends(get_conexao)):
    return servico.criar_usuario(conn, corpo.nome, corpo.email, corpo.senha, corpo.perfil)


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioSaida, tags=["Usuários"],
              summary="Alterar ou inativar usuário (gestor)",
              description="Envie só os campos a mudar. `ativo=false` inativa e libera o guichê que o usuário ocupa.",
              responses=respostas(401, 403, 404, 409, 422, 503))
def atualizar_usuario(corpo: UsuarioAtualizar, usuario_id: IdRecurso,
                      ator: UsuarioAtual = Depends(somente_gestor), conn: Connection = Depends(get_conexao)):
    return servico.atualizar_usuario(conn, ator, usuario_id, corpo.model_dump(exclude_unset=True))
