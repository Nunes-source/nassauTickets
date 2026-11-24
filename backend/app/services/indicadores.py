"""Indicadores de desempenho (RF-16; definições em docs/requirements/02 §4)."""
from datetime import date

from pymysql.connections import Connection

from app.core import periodos
from app.core.errors import ErroNegocio
from app.core.tempo import horas_de_expediente, hoje
from app.repositories import relatorios as repo

TIPOS_SENHA = ("SP", "SE", "SG")


def _medias(linhas: list[dict]) -> dict:
    medias = {t: None for t in TIPOS_SENHA}
    for linha in linhas:
        medias[linha["tipo"]] = None if linha["media_seg"] is None else int(round(float(linha["media_seg"])))
    return medias


def calcular(conn: Connection, de: date | None, ate: date | None) -> dict:
    de = de or hoje()
    ate = ate or de
    try:
        periodos.validar_intervalo(de, ate)
    except ValueError as erro:
        raise ErroNegocio("VALIDACAO", str(erro), 422)

    contagem = repo.contagem_nao_comparecimento(conn, de, ate)
    emitidas = int(contagem["emitidas"] or 0)
    abandonadas = int(contagem["abandonadas"] or 0)
    # Vazão = atendimentos concluídos ÷ horas de expediente de todos os dias do intervalo.
    horas = horas_de_expediente() * periodos.dias_no_intervalo(de, ate)

    return {
        "de": de.isoformat(),
        "ate": ate.isoformat(),
        "tempo_medio_espera_seg": _medias(repo.espera_media_por_tipo(conn, de, ate)),
        "tempo_medio_atendimento_seg": _medias(repo.atendimento_medio_por_tipo(conn, de, ate)),
        "taxa_nao_comparecimento": round(abandonadas / emitidas, 4) if emitidas else 0.0,
        "atendimentos_por_guiche": [
            {"guiche": l["guiche"], "quantidade": int(l["quantidade"])}
            for l in repo.atendimentos_por_guiche(conn, de, ate)],
        "atendimentos_por_atendente": [
            {"atendente": l["atendente"], "quantidade": int(l["quantidade"])}
            for l in repo.atendimentos_por_atendente(conn, de, ate)],
        "vazao_por_hora": round(repo.total_atendidas(conn, de, ate) / horas, 2) if horas else 0.0,
    }
