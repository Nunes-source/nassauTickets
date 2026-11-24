"""Relatórios e indicadores (contrato §5). Somente GESTOR."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pymysql.connections import Connection

from app.core.db import get_conexao
from app.core.security import UsuarioAtual, exigir_perfil
from app.schemas.comum import respostas
from app.services import indicadores as servico_indicadores
from app.services import relatorios as servico

router = APIRouter()
somente_gestor = exigir_perfil("GESTOR")

_EXEMPLOS = {
    "resumo": {"summary": "tipo=resumo", "value": {
        "periodo": "2026-11-27", "emitidas_total": 120, "atendidas_total": 98, "nao_compareceu_total": 22,
        "por_tipo": {"SP": {"emitidas": 20, "atendidas": 18}, "SE": {"emitidas": 40, "atendidas": 38},
                     "SG": {"emitidas": 60, "atendidas": 42}}}},
    "senhas": {"summary": "tipo=senhas", "value": {
        "periodo": "2026-11-27", "pagina": 1, "tamanho": 50, "total": 120, "itens": [{
            "numero": "261127-SP001", "tipo": "SP", "emitida_em": "2026-11-27T07:01:10-03:00",
            "atendimento_inicio": "2026-11-27T07:05:00-03:00", "atendimento_fim": "2026-11-27T07:19:30-03:00",
            "guiche": 3}]}},
    "tm": {"summary": "tipo=tm", "value": {"periodo": "2026-11-27", "por_tipo": {
        "SP": {"quantidade": 18, "tm_simulado_medio_seg": 905, "tm_real_medio_seg": 910},
        "SE": {"quantidade": 38, "tm_simulado_medio_seg": 78, "tm_real_medio_seg": 80},
        "SG": {"quantidade": 42, "tm_simulado_medio_seg": 301, "tm_real_medio_seg": 298}}}},
    "auditoria": {"summary": "tipo=auditoria", "value": {
        "periodo": "2026-11-27", "pagina": 1, "tamanho": 50, "total": 120, "itens": [{
            "atendente": "Atendente 1", "guiche": 3, "senha": "261127-SP001",
            "primeira_chamada_em": "2026-11-27T07:05:00-03:00", "segunda_chamada_em": None,
            "inicio_atendimento_em": "2026-11-27T07:05:40-03:00",
            "fim_atendimento_em": "2026-11-27T07:19:30-03:00"}]}},
}


@router.get("/relatorios/{periodo}/{tipo}", tags=["Relatórios"], summary="Relatórios diário e mensal",
            description=(
                "- `periodo=diario`: use `data` (padrão: hoje). `periodo=mensal`: use `ano` e `mes` (padrão: mês atual).\n"
                "- `tipo`: `resumo` (RF-15 a, b), `senhas` (c), `tm` (d) ou `auditoria` (e).\n"
                "- `senhas` e `auditoria` são paginados (`pagina`, `tamanho`)."),
            response_model=None,
            responses={**respostas(401, 403, 422, 503),
                       200: {"description": "O formato depende do `tipo`.",
                             "content": {"application/json": {"examples": _EXEMPLOS}}}})
def relatorio(
    periodo: Literal["diario", "mensal"],
    tipo: Literal["resumo", "senhas", "tm", "auditoria"],
    data: date | None = Query(None, description="Dia do relatório diário (AAAA-MM-DD)."),
    ano: int | None = Query(None, description="Ano do relatório mensal."),
    mes: int | None = Query(None, description="Mês do relatório mensal (1 a 12)."),
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(50, ge=1, le=200),
    _: UsuarioAtual = Depends(somente_gestor),
    conn: Connection = Depends(get_conexao),
):
    return servico.gerar(conn, periodo, tipo, data, ano, mes, pagina, tamanho)


@router.get("/indicadores", tags=["Relatórios"], summary="Indicadores de desempenho (RF-16)",
            description="Seis indicadores no intervalo `de`..`ate` (padrão: hoje; máximo de 366 dias). "
                        "Vazão = atendimentos concluídos ÷ horas de expediente do intervalo.",
            response_model=None,
            responses={**respostas(401, 403, 422, 503),
                       200: {"content": {"application/json": {"example": {
                           "de": "2026-11-27", "ate": "2026-11-27",
                           "tempo_medio_espera_seg": {"SP": 120, "SE": 300, "SG": 900},
                           "tempo_medio_atendimento_seg": {"SP": 890, "SE": 75, "SG": 310},
                           "taxa_nao_comparecimento": 0.05,
                           "atendimentos_por_guiche": [{"guiche": 1, "quantidade": 40}],
                           "atendimentos_por_atendente": [{"atendente": "Atendente 1", "quantidade": 40}],
                           "vazao_por_hora": 9.8}}}}})
def indicadores(de: date | None = Query(None, description="Início (AAAA-MM-DD)."),
                ate: date | None = Query(None, description="Fim (AAAA-MM-DD)."),
                _: UsuarioAtual = Depends(somente_gestor), conn: Connection = Depends(get_conexao)):
    return servico_indicadores.calcular(conn, de, ate)
