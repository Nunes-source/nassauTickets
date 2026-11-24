"""Relatórios (RF-15) e indicadores (RF-16) sobre dados conhecidos."""
from datetime import datetime
from pathlib import Path

import pytest

from database.migrar import dividir_sql
from tests.conftest import API

DIA = "2026-11-27"


def _t(h, m=0, s=0):
    return datetime(2026, 11, 27, h, m, s)


@pytest.fixture
def fila(ambiente, cliente):
    """Cria 4 senhas com histórico conhecido (precisa das tabelas do Dev A; usa a cópia de teste se faltarem)."""
    with ambiente.cursor() as cur:
        cur.execute("SHOW TABLES LIKE 'senhas'")
        if cur.fetchone() is None:
            for comando in dividir_sql((Path(__file__).parent / "schema_fila_teste.sql").read_text(encoding="utf-8")):
                cur.execute(comando)
    ambiente.commit()

    with ambiente.cursor() as cur:
        cur.execute("SELECT id, email FROM usuarios")
        usuario = {u["email"]: u["id"] for u in cur.fetchall()}
        cur.execute("SELECT id, numero FROM guiches")
        guiche = {g["numero"]: g["id"] for g in cur.fetchall()}
        at1, at2 = usuario["atendente1@nassau.local"], usuario["atendente2@nassau.local"]

        def senha(numero, tipo, seq, estado, emitida, motivo=None):
            cur.execute("INSERT INTO senhas (numero, data_emissao, tipo, sequencia, estado, motivo_descarte, emitida_em) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)", (numero, DIA, tipo, seq, estado, motivo, emitida))
            return cur.lastrowid

        def chamada(sid, g, u, n, quando):
            cur.execute("INSERT INTO chamadas (senha_id, guiche_id, usuario_id, numero_chamada, chamada_em) "
                        "VALUES (%s, %s, %s, %s, %s)", (sid, g, u, n, quando))

        def atendimento(sid, g, u, ini, fim, simulada):
            cur.execute("INSERT INTO atendimentos (senha_id, guiche_id, usuario_id, iniciado_em, finalizado_em, "
                        "duracao_simulada_seg) VALUES (%s, %s, %s, %s, %s, %s)", (sid, g, u, ini, fim, simulada))

        sp = senha("261127-SP001", "SP", 1, "ATENDIDA", _t(7, 0))
        chamada(sp, guiche[1], at1, 1, _t(7, 5))
        atendimento(sp, guiche[1], at1, _t(7, 5, 30), _t(7, 20, 30), 900)

        se = senha("261127-SE001", "SE", 1, "ATENDIDA", _t(7, 1))
        chamada(se, guiche[2], at2, 1, _t(7, 3))
        atendimento(se, guiche[2], at2, _t(7, 3, 10), _t(7, 4, 10), 60)

        sg1 = senha("261127-SG001", "SG", 1, "NAO_COMPARECEU", _t(7, 2), "ABANDONO")
        chamada(sg1, guiche[1], at1, 1, _t(7, 10))
        chamada(sg1, guiche[1], at1, 2, _t(7, 12))

        senha("261127-SG002", "SG", 2, "NAO_COMPARECEU", _t(16, 59), "FIM_EXPEDIENTE")
    ambiente.commit()


def _get(cliente, gestor, rota, **params):
    return cliente.get(f"{API}{rota}", params=params, headers=gestor)


def test_resumo_diario(cliente, gestor, fila):
    corpo = _get(cliente, gestor, "/relatorios/diario/resumo", data=DIA).json()
    assert corpo == {
        "periodo": DIA, "emitidas_total": 4, "atendidas_total": 2, "nao_compareceu_total": 2,
        "por_tipo": {"SP": {"emitidas": 1, "atendidas": 1}, "SE": {"emitidas": 1, "atendidas": 1},
                     "SG": {"emitidas": 2, "atendidas": 0}}}


def test_resumo_mensal_agrega_o_mes_e_ignora_outros(cliente, gestor, fila):
    novembro = _get(cliente, gestor, "/relatorios/mensal/resumo", ano=2026, mes=11).json()
    assert novembro["periodo"] == "2026-11" and novembro["emitidas_total"] == 4
    dezembro = _get(cliente, gestor, "/relatorios/mensal/resumo", ano=2026, mes=12).json()
    assert dezembro["emitidas_total"] == 0 and dezembro["por_tipo"]["SP"] == {"emitidas": 0, "atendidas": 0}


def test_senhas_detalhado_com_paginacao(cliente, gestor, fila):
    corpo = _get(cliente, gestor, "/relatorios/diario/senhas", data=DIA).json()
    assert corpo["total"] == 4 and len(corpo["itens"]) == 4
    primeira, nao_atendida = corpo["itens"][0], corpo["itens"][2]
    assert primeira["numero"] == "261127-SP001" and primeira["guiche"] == 1
    assert primeira["atendimento_inicio"] == "2026-11-27T07:05:30-03:00"
    assert nao_atendida["numero"] == "261127-SG001"
    assert nao_atendida["atendimento_inicio"] is None and nao_atendida["guiche"] is None
    pagina2 = _get(cliente, gestor, "/relatorios/diario/senhas", data=DIA, pagina=2, tamanho=3).json()
    assert pagina2["total"] == 4 and [i["numero"] for i in pagina2["itens"]] == ["261127-SG002"]


def test_tm_por_tipo(cliente, gestor, fila):
    por_tipo = _get(cliente, gestor, "/relatorios/diario/tm", data=DIA).json()["por_tipo"]
    assert por_tipo["SP"] == {"quantidade": 1, "tm_simulado_medio_seg": 900, "tm_real_medio_seg": 900}
    assert por_tipo["SE"] == {"quantidade": 1, "tm_simulado_medio_seg": 60, "tm_real_medio_seg": 60}
    assert por_tipo["SG"] == {"quantidade": 0, "tm_simulado_medio_seg": None, "tm_real_medio_seg": None}


def test_auditoria_inclui_primeira_e_segunda_chamada_e_nao_comparecimentos(cliente, gestor, fila):
    corpo = _get(cliente, gestor, "/relatorios/diario/auditoria", data=DIA).json()
    assert corpo["total"] == 3  # SG002 nunca foi chamada
    por_senha = {i["senha"]: i for i in corpo["itens"]}
    sp = por_senha["261127-SP001"]
    assert sp["atendente"] == "Atendente 1" and sp["guiche"] == 1
    assert sp["primeira_chamada_em"] == "2026-11-27T07:05:00-03:00" and sp["segunda_chamada_em"] is None
    assert sp["inicio_atendimento_em"] == "2026-11-27T07:05:30-03:00"
    assert sp["fim_atendimento_em"] == "2026-11-27T07:20:30-03:00"
    sg = por_senha["261127-SG001"]
    assert sg["segunda_chamada_em"] == "2026-11-27T07:12:00-03:00"
    assert sg["inicio_atendimento_em"] is None and sg["fim_atendimento_em"] is None


def test_indicadores(cliente, gestor, fila):
    corpo = _get(cliente, gestor, "/indicadores", de=DIA, ate=DIA).json()
    assert corpo["tempo_medio_espera_seg"] == {"SP": 300, "SE": 120, "SG": 480}
    assert corpo["tempo_medio_atendimento_seg"] == {"SP": 900, "SE": 60, "SG": None}
    assert corpo["taxa_nao_comparecimento"] == 0.25  # só ABANDONO conta: 1 de 4
    assert corpo["atendimentos_por_guiche"] == [{"guiche": 1, "quantidade": 1}, {"guiche": 2, "quantidade": 1}]
    assert corpo["atendimentos_por_atendente"] == [{"atendente": "Atendente 1", "quantidade": 1},
                                                   {"atendente": "Atendente 2", "quantidade": 1}]
    assert corpo["vazao_por_hora"] == 0.2  # 2 atendimentos ÷ 10 h de expediente


def test_indicadores_sem_dados_nao_dividem_por_zero(cliente, gestor, fila):
    corpo = _get(cliente, gestor, "/indicadores", de="2026-01-01", ate="2026-01-01").json()
    assert corpo["taxa_nao_comparecimento"] == 0.0 and corpo["vazao_por_hora"] == 0.0
    assert corpo["tempo_medio_espera_seg"] == {"SP": None, "SE": None, "SG": None}


@pytest.mark.parametrize("rota,params", [
    ("/relatorios/mensal/resumo", {"ano": 2026, "mes": 13}),
    ("/relatorios/mensal/resumo", {"ano": 1990, "mes": 1}),
    ("/indicadores", {"de": "2026-11-30", "ate": "2026-11-01"}),
    ("/indicadores", {"de": "2024-01-01", "ate": "2026-11-01"}),
    ("/relatorios/diario/resumo", {"data": "27/11/2026"}),
    ("/relatorios/semanal/resumo", {}),
    ("/relatorios/diario/senhas", {"tamanho": 0}),
])
def test_periodo_invalido_e_422(cliente, gestor, fila, rota, params):
    resposta = _get(cliente, gestor, rota, **params)
    assert resposta.status_code == 422 and resposta.json()["codigo"] == "VALIDACAO"


def test_relatorios_exigem_token_e_perfil_de_gestor(cliente, atendente1, fila):
    assert cliente.get(f"{API}/relatorios/diario/resumo").status_code == 401
    assert cliente.get(f"{API}/relatorios/diario/resumo", headers=atendente1).status_code == 403
