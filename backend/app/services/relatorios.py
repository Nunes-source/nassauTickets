"""Relatórios diário e mensal (RF-15)."""
from datetime import date

from pymysql.connections import Connection

from app.core import periodos
from app.core.errors import ErroNegocio
from app.core.tempo import com_fuso, hoje
from app.repositories import relatorios as repo

TIPOS_SENHA = ("SP", "SE", "SG")


def resolver_periodo(periodo: str, data: date | None, ano: int | None, mes: int | None):
    """Devolve (de, ate, rótulo). Diário usa `data`; mensal usa `ano` e `mes` (padrão: hoje)."""
    referencia = hoje()
    try:
        if periodo == "diario":
            return periodos.intervalo_diario(data or referencia)
        return periodos.intervalo_mensal(ano or referencia.year, mes or referencia.month)
    except ValueError as erro:
        raise ErroNegocio("VALIDACAO", str(erro), 422)


def _inteiro(valor) -> int:
    return int(valor or 0)


def _segundos(valor) -> int | None:
    return None if valor is None else int(round(float(valor)))


def _pagina(pagina: int, tamanho: int) -> tuple[int, int]:
    return tamanho, (pagina - 1) * tamanho


def resumo(conn: Connection, de: date, ate: date, rotulo: str) -> dict:
    por_tipo = {t: {"emitidas": 0, "atendidas": 0} for t in TIPOS_SENHA}
    nao_compareceu = 0
    for linha in repo.resumo_por_tipo(conn, de, ate):
        por_tipo[linha["tipo"]] = {"emitidas": _inteiro(linha["emitidas"]), "atendidas": _inteiro(linha["atendidas"])}
        nao_compareceu += _inteiro(linha["nao_compareceu"])
    return {
        "periodo": rotulo,
        "emitidas_total": sum(v["emitidas"] for v in por_tipo.values()),
        "atendidas_total": sum(v["atendidas"] for v in por_tipo.values()),
        "nao_compareceu_total": nao_compareceu,
        "por_tipo": por_tipo,
    }


def senhas(conn: Connection, de: date, ate: date, rotulo: str, pagina: int, tamanho: int) -> dict:
    limite, deslocamento = _pagina(pagina, tamanho)
    itens = [
        {**l, "emitida_em": com_fuso(l["emitida_em"]),
         "atendimento_inicio": com_fuso(l["atendimento_inicio"]),
         "atendimento_fim": com_fuso(l["atendimento_fim"])}
        for l in repo.listar_senhas(conn, de, ate, limite, deslocamento)
    ]
    return {"periodo": rotulo, "pagina": pagina, "tamanho": tamanho,
            "total": repo.contar_senhas(conn, de, ate), "itens": itens}


def tm(conn: Connection, de: date, ate: date, rotulo: str) -> dict:
    por_tipo = {t: {"quantidade": 0, "tm_simulado_medio_seg": None, "tm_real_medio_seg": None}
                for t in TIPOS_SENHA}
    for linha in repo.tm_por_tipo(conn, de, ate):
        por_tipo[linha["tipo"]] = {
            "quantidade": _inteiro(linha["quantidade"]),
            "tm_simulado_medio_seg": _segundos(linha["tm_simulado_medio_seg"]),
            "tm_real_medio_seg": _segundos(linha["tm_real_medio_seg"]),
        }
    return {"periodo": rotulo, "por_tipo": por_tipo}


def auditoria(conn: Connection, de: date, ate: date, rotulo: str, pagina: int, tamanho: int) -> dict:
    limite, deslocamento = _pagina(pagina, tamanho)
    itens = [
        {**l, **{c: com_fuso(l[c]) for c in ("primeira_chamada_em", "segunda_chamada_em",
                                              "inicio_atendimento_em", "fim_atendimento_em")}}
        for l in repo.listar_auditoria(conn, de, ate, limite, deslocamento)
    ]
    return {"periodo": rotulo, "pagina": pagina, "tamanho": tamanho,
            "total": repo.contar_auditoria(conn, de, ate), "itens": itens}


def gerar(conn: Connection, periodo: str, tipo: str, data: date | None, ano: int | None,
          mes: int | None, pagina: int, tamanho: int) -> dict:
    de, ate, rotulo = resolver_periodo(periodo, data, ano, mes)
    if tipo == "resumo":
        return resumo(conn, de, ate, rotulo)
    if tipo == "senhas":
        return senhas(conn, de, ate, rotulo, pagina, tamanho)
    if tipo == "tm":
        return tm(conn, de, ate, rotulo)
    return auditoria(conn, de, ate, rotulo, pagina, tamanho)
