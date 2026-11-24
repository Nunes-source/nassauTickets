"""Usuários e guichês: cadastro, ocupação e liberação (RN-11, RN-13)."""
import pymysql
from pymysql.connections import Connection

from app.core.db import transacao
from app.core.errors import ErroNegocio
from app.core.security import UsuarioAtual, gerar_hash
from app.core.tempo import hoje
from app.repositories import guiches as repo_guiches
from app.repositories import usuarios as repo_usuarios

# Nome do índice UNIQUE que causou o erro -> erro de negócio equivalente.
_INDICES = {
    "uq_usuarios_email": ("EMAIL_JA_CADASTRADO", "Já existe um usuário com este e-mail."),
    "uq_gestor_unico": ("GESTOR_JA_EXISTE", "Já existe um GESTOR ativo."),
    "uq_guiches_numero": ("GUICHE_JA_CADASTRADO", "Já existe um guichê com este número."),
    "uq_guiches_usuario": ("ATENDENTE_JA_TEM_GUICHE", "Este atendente já ocupa outro guichê."),
}


def _erro_de_integridade(erro: pymysql.err.IntegrityError) -> Exception:
    """Rede de segurança contra corrida: o banco garante a unicidade mesmo se duas requisições passarem
    pela checagem ao mesmo tempo."""
    texto = str(erro)
    for indice, (codigo, mensagem) in _INDICES.items():
        if indice in texto:
            return ErroNegocio(codigo, mensagem, 409)
    return erro


# ---------------------------------------------------------------- usuários

def _usuario_publico(linha: dict) -> dict:
    return {"id": linha["id"], "nome": linha["nome"], "email": linha["email"],
            "perfil": linha["perfil"], "ativo": bool(linha["ativo"])}


def listar_usuarios(conn: Connection) -> list[dict]:
    return [_usuario_publico(u) for u in repo_usuarios.listar(conn)]


def criar_usuario(conn: Connection, nome: str, email: str, senha: str, perfil: str) -> dict:
    senha_hash = gerar_hash(senha)  # fora da transação: argon2 é lento de propósito
    try:
        with transacao(conn):
            if repo_usuarios.email_em_uso(conn, email):
                raise ErroNegocio(*_INDICES["uq_usuarios_email"], 409)
            if perfil == "GESTOR" and repo_usuarios.existe_gestor_ativo(conn):
                raise ErroNegocio(*_INDICES["uq_gestor_unico"], 409)
            novo_id = repo_usuarios.inserir(conn, nome, email, senha_hash, perfil)
            linha = repo_usuarios.buscar_por_id(conn, novo_id)
    except pymysql.err.IntegrityError as erro:
        raise _erro_de_integridade(erro)
    return _usuario_publico(linha)


def atualizar_usuario(conn: Connection, ator: UsuarioAtual, usuario_id: int, mudancas: dict) -> dict:
    nova_hash = gerar_hash(mudancas["senha"]) if mudancas.get("senha") else None
    try:
        with transacao(conn):
            alvo = repo_usuarios.buscar_por_id(conn, usuario_id, para_atualizar=True)
            if alvo is None:
                raise ErroNegocio("NAO_ENCONTRADO", "Usuário não encontrado.", 404)
            perfil = mudancas.get("perfil") or alvo["perfil"]
            ativo = bool(alvo["ativo"]) if mudancas.get("ativo") is None else mudancas["ativo"]

            if alvo["id"] == ator.id and (not ativo or perfil != alvo["perfil"]):
                raise ErroNegocio("AUTOALTERACAO_PROIBIDA",
                                  "Você não pode inativar a si mesmo nem mudar o próprio perfil.", 409)
            email = mudancas.get("email")
            if email and repo_usuarios.email_em_uso(conn, email, excluir_id=usuario_id):
                raise ErroNegocio(*_INDICES["uq_usuarios_email"], 409)
            if perfil == "GESTOR" and ativo and repo_usuarios.existe_gestor_ativo(conn, excluir_id=usuario_id):
                raise ErroNegocio(*_INDICES["uq_gestor_unico"], 409)

            if alvo["ativo"] and not ativo:  # inativar libera o guichê que ele ocupa
                guiche = repo_guiches.buscar_por_usuario(conn, usuario_id)
                if guiche:
                    _exigir_sem_senha_ativa(conn, guiche["id"])
                    repo_guiches.definir_ocupante(conn, guiche["id"], None)

            campos = {k: mudancas[k] for k in ("nome", "email", "perfil", "ativo")
                      if mudancas.get(k) is not None}
            if nova_hash:
                campos["senha_hash"] = nova_hash
            repo_usuarios.atualizar(conn, usuario_id, campos)
            linha = repo_usuarios.buscar_por_id(conn, usuario_id)
    except pymysql.err.IntegrityError as erro:
        raise _erro_de_integridade(erro)
    return _usuario_publico(linha)


# ----------------------------------------------------------------- guichês

def _guiche_publico(linha: dict) -> dict:
    ocupado = linha["usuario_id"] is not None
    return {
        "id": linha["id"], "numero": linha["numero"], "ativo": bool(linha["ativo"]),
        "livre": bool(linha["ativo"]) and not ocupado,
        "ocupante": {"id": linha["usuario_id"], "nome": linha["ocupante_nome"]} if ocupado else None,
    }


def _exigir_sem_senha_ativa(conn: Connection, guiche_id: int) -> None:
    if repo_guiches.contar_senhas_ativas(conn, guiche_id, hoje()) > 0:
        raise ErroNegocio("GUICHE_COM_SENHA_ATIVA",
                          "O guichê ainda tem uma senha chamada ou em atendimento.", 409)


def listar_guiches(conn: Connection, apenas_livres: bool) -> list[dict]:
    return [_guiche_publico(g) for g in repo_guiches.listar(conn, apenas_livres)]


def criar_guiche(conn: Connection, numero: int) -> dict:
    try:
        with transacao(conn):
            if repo_guiches.numero_existe(conn, numero):
                raise ErroNegocio(*_INDICES["uq_guiches_numero"], 409)
            novo_id = repo_guiches.inserir(conn, numero)
            linha = repo_guiches.buscar_por_id(conn, novo_id)
    except pymysql.err.IntegrityError as erro:
        raise _erro_de_integridade(erro)
    return _guiche_publico(linha)


def atualizar_guiche(conn: Connection, guiche_id: int, ativo: bool) -> dict:
    with transacao(conn):
        guiche = repo_guiches.buscar_por_id(conn, guiche_id, para_atualizar=True)
        if guiche is None:
            raise ErroNegocio("NAO_ENCONTRADO", "Guichê não encontrado.", 404)
        if not ativo and guiche["usuario_id"] is not None:
            raise ErroNegocio("GUICHE_OCUPADO", "Libere o guichê antes de desativá-lo.", 409)
        repo_guiches.definir_ativo(conn, guiche_id, ativo)
        linha = repo_guiches.buscar_por_id(conn, guiche_id)
    return _guiche_publico(linha)


def ocupar_guiche(conn: Connection, guiche_id: int, usuario: UsuarioAtual) -> dict:
    try:
        with transacao(conn):
            guiche = repo_guiches.buscar_por_id(conn, guiche_id, para_atualizar=True)  # trava a linha
            if guiche is None:
                raise ErroNegocio("NAO_ENCONTRADO", "Guichê não encontrado.", 404)
            if not guiche["ativo"]:
                raise ErroNegocio("GUICHE_INATIVO", "Este guichê está desativado.", 409)
            if guiche["usuario_id"] == usuario.id:
                return _guiche_publico(guiche)  # já é dele: operação idempotente
            if guiche["usuario_id"] is not None:
                raise ErroNegocio("GUICHE_OCUPADO", "Este guichê já está ocupado por outro atendente.", 409)
            outro = repo_guiches.buscar_por_usuario(conn, usuario.id)
            if outro is not None:
                raise ErroNegocio("ATENDENTE_JA_TEM_GUICHE",
                                  "Você já ocupa outro guichê. Libere-o antes.", 409,
                                  {"guiche": outro["numero"]})
            repo_guiches.definir_ocupante(conn, guiche_id, usuario.id)
            linha = repo_guiches.buscar_por_id(conn, guiche_id)
    except pymysql.err.IntegrityError as erro:
        raise _erro_de_integridade(erro)
    return _guiche_publico(linha)


def liberar_guiche(conn: Connection, guiche_id: int, usuario: UsuarioAtual) -> dict:
    with transacao(conn):
        guiche = repo_guiches.buscar_por_id(conn, guiche_id, para_atualizar=True)
        if guiche is None:
            raise ErroNegocio("NAO_ENCONTRADO", "Guichê não encontrado.", 404)
        if guiche["usuario_id"] is None:
            return _guiche_publico(guiche)  # já estava livre
        if guiche["usuario_id"] != usuario.id and usuario.perfil != "GESTOR":
            raise ErroNegocio("SEM_PERMISSAO", "Só o ocupante (ou o gestor) pode liberar o guichê.", 403)
        _exigir_sem_senha_ativa(conn, guiche_id)
        repo_guiches.definir_ocupante(conn, guiche_id, None)
        linha = repo_guiches.buscar_por_id(conn, guiche_id)
    return _guiche_publico(linha)
