"""Regras da fila: escolha do próximo tipo (ADR-003), resumo, painel e descarte do fim do expediente."""
import logging
from datetime import timedelta

from pymysql.connections import Connection

from app.core import tempo
from app.core.db import transacao
from app.repositories import fila_estado as repo_fila
from app.repositories import senhas as repo_senhas
from app.services import estados

logger = logging.getLogger("nassau.fila")

TIPOS = ("SP", "SE", "SG")  # ordem = prioridade (RN-01): SP > SE > SG


def escolher_tipo(ultimo_tipo: str | None, disponiveis) -> str | None:
    """Decide de que tipo é a próxima senha. Função pura (ADR-003).

    1. Nada disponível -> None (FILA_VAZIA).
    2. Candidatos = disponíveis menos o último tipo chamado (nunca repete se houver outro).
    3. Sem candidatos, só o último tipo tem fila: usa ele.
    4. Entre os candidatos vale SP > SE > SG.
    """
    disponiveis = set(disponiveis)
    if not disponiveis:
        return None
    candidatos = disponiveis - {ultimo_tipo}
    if not candidatos:
        return ultimo_tipo
    return next(t for t in TIPOS if t in candidatos)


def resumo(conn: Connection) -> dict:
    garantir_descarte(conn)
    contagem = {t: 0 for t in TIPOS}
    for linha in repo_senhas.contar_aguardando_por_tipo(conn, tempo.hoje()):
        contagem[linha["tipo"]] = int(linha["total"])
    return contagem


def painel(conn: Connection) -> dict:
    """As 5 últimas senhas chamadas, mais recente primeiro. Nunca inclui a próxima (RN-09)."""
    garantir_descarte(conn)
    ultimas = [
        {
            "numero": l["numero"], "tipo": l["tipo"], "sequencial": l["sequencia"], "guiche": l["guiche"],
            "chamada": l["numero_chamada"], "ultima_chamada": l["numero_chamada"] == 2,
            "chamada_em": tempo.com_fuso(l["chamada_em"]),
        }
        for l in repo_senhas.listar_painel(conn, tempo.hoje(), 5)
    ]
    return {"ultimas": ultimas, "atualizado_em": tempo.agora()}


def garantir_descarte(conn: Connection) -> int:
    """RN-10 / UC-14: depois do fim do expediente, as senhas AGUARDANDO do dia viram
    NAO_COMPARECEU (motivo FIM_EXPEDIENTE). Roda na primeira requisição depois das 17h; é idempotente.

    Pega o mesmo lock do "chamar próximo", então nunca disputa uma senha com uma chamada em curso.
    Devolve quantas senhas foram descartadas.
    """
    if not tempo.depois_do_expediente():
        return 0
    dia = tempo.hoje()
    conn.commit()  # encerra qualquer transação anterior antes de pegar o lock
    if not repo_senhas.existe_aguardando(conn, dia):
        return 0
    with transacao(conn):
        repo_fila.garantir_linha(conn, dia)
        repo_fila.travar_e_ler(conn, dia)
        estados.validar_transicao(estados.AGUARDANDO, estados.NAO_COMPARECEU, estados.FIM_EXPEDIENTE)
        quando = tempo.agora_sem_fuso()
        repo_senhas.registrar_historico_descarte(conn, dia, quando)  # antes do UPDATE: lê o estado anterior
        descartadas = repo_senhas.descartar_aguardando(conn, dia)
    if descartadas:
        logger.info("descarte de fim de expediente: %d senha(s)", descartadas)
    return descartadas
