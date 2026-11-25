"""Chamar próximo/novamente, iniciar, encerrar e registrar não comparecimento (RF-04 a RF-08).

Toda operação roda numa transação explícita (ADR-002) e grava o histórico da senha (RNF-06).
"""
from datetime import datetime

from pymysql.connections import Connection

from app.core import tempo
from app.core.db import transacao
from app.core.errors import ErroNegocio
from app.core.security import UsuarioAtual
from app.repositories import atendimentos as repo_atendimentos
from app.repositories import chamadas as repo_chamadas
from app.repositories import fila_estado as repo_fila
from app.repositories import guiches as repo_guiches
from app.repositories import senhas as repo_senhas
from app.services import anuncio, estados, fila, simulacao


# ------------------------------------------------------------ respostas

def _senha(senha: dict, estado: str) -> dict:
    return {"id": senha["id"], "numero": senha["numero"], "tipo": senha["tipo"],
            "sequencial": senha["sequencia"], "estado": estado}


def _resposta_chamada(senha: dict, estado: str, guiche_id: int, guiche_numero: int, numero_chamada: int,
                      quando: datetime) -> dict:
    ultima = numero_chamada == 2
    return {
        "senha": _senha(senha, estado),
        "guiche": {"id": guiche_id, "numero": guiche_numero},
        "chamada": {"numero": numero_chamada, "ultima_chamada": ultima, "chamada_em": tempo.com_fuso(quando)},
        "texto_chamada": anuncio.texto_chamada(senha["tipo"], senha["sequencia"], guiche_numero, ultima),
    }


# ------------------------------------------------------- chamar próximo

def chamar_proximo(conn: Connection, usuario: UsuarioAtual) -> dict:
    """RF-04. Serializa as chamadas com o lock da linha do dia em `fila_estado` (ADR-002)."""
    fila.garantir_descarte(conn)
    if not tempo.dentro_do_expediente():
        raise ErroNegocio("FORA_DO_EXPEDIENTE", "Fora do expediente (07h às 17h): não é possível chamar.", 409)
    guiche = repo_guiches.buscar_por_usuario(conn, usuario.id)
    if guiche is None:
        raise ErroNegocio("ATENDENTE_SEM_GUICHE", "Ocupe um guichê antes de chamar uma senha.", 409)

    dia = tempo.hoje()
    conn.commit()  # a transação começa limpa: tudo abaixo é lido DEPOIS de obter o lock
    with transacao(conn):
        repo_fila.garantir_linha(conn, dia)
        ultimo_tipo = repo_fila.travar_e_ler(conn, dia)  # as outras chamadas esperam aqui
        if repo_guiches.contar_senhas_ativas(conn, guiche["id"], dia) > 0:  # RN-12
            raise ErroNegocio("GUICHE_COM_SENHA_ATIVA",
                              "Este guichê ainda tem uma senha chamada ou em atendimento.", 409)
        tipo = fila.escolher_tipo(ultimo_tipo, repo_senhas.tipos_aguardando(conn, dia))  # ADR-003
        senha = repo_senhas.proxima_aguardando(conn, dia, tipo) if tipo else None
        if senha is None:
            raise ErroNegocio("FILA_VAZIA", "Não há senhas aguardando.", 404)

        quando = tempo.agora_sem_fuso()  # depois do lock: a ordem do horário acompanha a ordem das chamadas
        estados.validar_transicao(estados.AGUARDANDO, estados.CHAMADA)
        repo_senhas.atualizar_estado(conn, senha["id"], estados.CHAMADA)
        repo_chamadas.inserir(conn, senha["id"], guiche["id"], usuario.id, 1, quando)
        repo_senhas.registrar_historico(conn, senha["id"], estados.AGUARDANDO, estados.CHAMADA,
                                        usuario.id, "ATENDENTE", quando)
        repo_fila.definir_ultimo_tipo(conn, dia, tipo)
    return _resposta_chamada(senha, estados.CHAMADA, guiche["id"], guiche["numero"], 1, quando)


# ------------------------------------------------ ações sobre uma senha

def _carregar(conn: Connection, senha_id: int) -> tuple[dict, dict | None]:
    """Senha travada (FOR UPDATE) e sua chamada mais recente. Chamar DENTRO da transação."""
    senha = repo_senhas.buscar_por_id(conn, senha_id, para_atualizar=True)
    if senha is None:
        raise ErroNegocio("NAO_ENCONTRADO", "Senha não encontrada.", 404)
    return senha, repo_chamadas.ultima_da_senha(conn, senha_id)


def _exigir_responsavel(usuario: UsuarioAtual, ultima: dict) -> None:
    """Só quem chamou a senha (ou o gestor, como supervisor) mexe nela."""
    if ultima["usuario_id"] != usuario.id and usuario.perfil != "GESTOR":
        raise ErroNegocio("SEM_PERMISSAO", "Esta senha foi chamada por outro atendente.", 403)


def _transitar(conn: Connection, usuario: UsuarioAtual, senha: dict, novo: str, quando: datetime,
               motivo: str | None = None) -> None:
    repo_senhas.atualizar_estado(conn, senha["id"], novo, motivo)
    repo_senhas.registrar_historico(conn, senha["id"], senha["estado"], novo, usuario.id, "ATENDENTE", quando)


def chamar_novamente(conn: Connection, usuario: UsuarioAtual, senha_id: int) -> dict:
    """RF-05 / RN-15: só de CHAMADA, só uma vez, no mesmo guichê.

    Vale também depois das 17h: a senha já foi chamada antes do fim do expediente e precisa
    poder terminar (RN-10: o que está em curso pode ser concluído).
    """
    conn.commit()
    with transacao(conn):
        senha, ultima = _carregar(conn, senha_id)
        estados.validar_transicao(senha["estado"], estados.CHAMADA_NOVAMENTE)
        _exigir_responsavel(usuario, ultima)
        quando = tempo.agora_sem_fuso()
        repo_chamadas.inserir(conn, senha_id, ultima["guiche_id"], ultima["usuario_id"], 2, quando)
        _transitar(conn, usuario, senha, estados.CHAMADA_NOVAMENTE, quando)
    return _resposta_chamada(senha, estados.CHAMADA_NOVAMENTE, ultima["guiche_id"], ultima["guiche_numero"], 2, quando)


def iniciar_atendimento(conn: Connection, usuario: UsuarioAtual, senha_id: int) -> dict:
    """RF-06: CHAMADA ou CHAMADA_NOVAMENTE -> EM_ATENDIMENTO; sorteia o TM simulado (RN-07)."""
    conn.commit()
    with transacao(conn):
        senha, ultima = _carregar(conn, senha_id)
        estados.validar_transicao(senha["estado"], estados.EM_ATENDIMENTO)
        _exigir_responsavel(usuario, ultima)
        quando = tempo.agora_sem_fuso()
        duracao = simulacao.sortear_duracao(senha["tipo"])
        repo_atendimentos.inserir(conn, senha_id, ultima["guiche_id"], usuario.id, quando, duracao)
        _transitar(conn, usuario, senha, estados.EM_ATENDIMENTO, quando)
    return {"senha": _senha(senha, estados.EM_ATENDIMENTO), "duracao_simulada_seg": duracao}


def encerrar_atendimento(conn: Connection, usuario: UsuarioAtual, senha_id: int) -> dict:
    """RF-07: EM_ATENDIMENTO -> ATENDIDA. Permitido depois das 17h (já estava em curso)."""
    conn.commit()
    with transacao(conn):
        senha, ultima = _carregar(conn, senha_id)
        estados.validar_transicao(senha["estado"], estados.ATENDIDA)
        _exigir_responsavel(usuario, ultima)
        quando = tempo.agora_sem_fuso()
        if repo_atendimentos.finalizar(conn, senha_id, quando) != 1:
            raise ErroNegocio("ERRO_INTERNO", "Atendimento em curso não encontrado.", 500)
        _transitar(conn, usuario, senha, estados.ATENDIDA, quando)
    return _senha(senha, estados.ATENDIDA)


def registrar_nao_comparecimento(conn: Connection, usuario: UsuarioAtual, senha_id: int) -> dict:
    """RF-08: só depois da 2ª chamada (CHAMADA_NOVAMENTE), motivo ABANDONO."""
    conn.commit()
    with transacao(conn):
        senha, ultima = _carregar(conn, senha_id)
        estados.validar_transicao(senha["estado"], estados.NAO_COMPARECEU, estados.ABANDONO)
        _exigir_responsavel(usuario, ultima)
        _transitar(conn, usuario, senha, estados.NAO_COMPARECEU, tempo.agora_sem_fuso(), estados.ABANDONO)
    return _senha(senha, estados.NAO_COMPARECEU)


# ------------------------------------------------- senha ativa do guichê

def atendimento_atual(conn: Connection, usuario: UsuarioAtual) -> dict | None:
    """Senha ativa (CHAMADA, CHAMADA_NOVAMENTE ou EM_ATENDIMENTO) do guichê do atendente, ou None.

    Só leitura. Existe para o front recuperar o estado depois de recarregar a página: sem isso o
    atendente ficaria preso em GUICHE_COM_SENHA_ATIVA sem saber qual senha encerrar.
    """
    guiche = repo_guiches.buscar_por_usuario(conn, usuario.id)
    if guiche is None:
        return None
    ativa = repo_chamadas.ativa_do_guiche(conn, guiche["id"], tempo.hoje())
    if ativa is None:
        return None
    return _resposta_chamada(ativa, ativa["estado"], ativa["guiche_id"], ativa["guiche_numero"],
                             ativa["numero_chamada"], ativa["chamada_em"])

