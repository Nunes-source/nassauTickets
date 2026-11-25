"""Emissão de senhas (RF-01 a RF-03, RN-02)."""
from datetime import date

from pymysql.connections import Connection

from app.core import tempo
from app.core.db import transacao
from app.core.errors import ErroNegocio
from app.repositories import senhas as repo_senhas
from app.services import estados, fila

SEQUENCIA_MAXIMA = 999


def formatar_numero(dia: date, tipo: str, sequencial: int) -> str:
    """`YYMMDD-PPSQ`, ex.: 2026-11-27, SP, 1 -> `261127-SP001` (12 caracteres)."""
    if tipo not in fila.TIPOS:
        raise ValueError(f"tipo inválido: {tipo!r}")
    if sequencial < 1:
        raise ValueError("a sequência começa em 1")
    if sequencial > SEQUENCIA_MAXIMA:
        raise ErroNegocio("SEQUENCIA_ESGOTADA",
                          f"Acabaram as senhas do tipo {tipo} de hoje (limite de {SEQUENCIA_MAXIMA}).", 409,
                          {"tipo": tipo})
    return f"{dia:%y%m%d}-{tipo}{sequencial:03d}"


def emitir_senha(conn: Connection, tipo: str) -> dict:
    """Totem emite a senha: contador atômico, EMITIDA -> AGUARDANDO e histórico na mesma transação."""
    fila.garantir_descarte(conn)  # primeira requisição depois das 17h limpa a fila antes de recusar
    if not tempo.dentro_do_expediente():
        raise ErroNegocio("FORA_DO_EXPEDIENTE", "Fora do expediente (07h às 17h): não é possível emitir senhas.", 409)

    dia = tempo.hoje()
    quando = tempo.agora_sem_fuso()
    conn.commit()  # a transação da emissão começa limpa
    with transacao(conn):
        sequencial = repo_senhas.proximo_sequencial(conn, dia, tipo)
        numero = formatar_numero(dia, tipo, sequencial)  # >999 levanta e desfaz o contador
        estados.validar_transicao(None, estados.EMITIDA)
        senha_id = repo_senhas.inserir(conn, numero, dia, tipo, sequencial, estados.EMITIDA, quando)
        repo_senhas.registrar_historico(conn, senha_id, None, estados.EMITIDA, None, "TOTEM", quando)
        estados.validar_transicao(estados.EMITIDA, estados.AGUARDANDO)
        repo_senhas.atualizar_estado(conn, senha_id, estados.AGUARDANDO)
        repo_senhas.registrar_historico(conn, senha_id, estados.EMITIDA, estados.AGUARDANDO, None, "SISTEMA", quando)
    return {"id": senha_id, "numero": numero, "tipo": tipo, "sequencial": sequencial,
            "estado": estados.AGUARDANDO, "emitida_em": tempo.com_fuso(quando)}
