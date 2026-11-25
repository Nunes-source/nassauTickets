"""Máquina de estados (RF-10, RN-14): todas as transições válidas e inválidas."""
import itertools

import pytest

from app.core.errors import ErroNegocio
from app.services import estados as e

VALIDAS = [
    (None, e.EMITIDA, None),
    (e.EMITIDA, e.AGUARDANDO, None),
    (e.AGUARDANDO, e.CHAMADA, None),
    (e.AGUARDANDO, e.NAO_COMPARECEU, e.FIM_EXPEDIENTE),
    (e.CHAMADA, e.CHAMADA_NOVAMENTE, None),
    (e.CHAMADA, e.EM_ATENDIMENTO, None),
    (e.CHAMADA_NOVAMENTE, e.EM_ATENDIMENTO, None),
    (e.CHAMADA_NOVAMENTE, e.NAO_COMPARECEU, e.ABANDONO),
    (e.EM_ATENDIMENTO, e.ATENDIDA, None),
]


def test_a_tabela_tem_exatamente_as_9_transicoes_do_diagrama():
    assert len(e.TRANSICOES) == 9
    assert set(e.TRANSICOES) == {(de, para) for de, para, _ in VALIDAS}


@pytest.mark.parametrize("de,para,motivo", VALIDAS)
def test_transicoes_validas_passam(de, para, motivo):
    e.validar_transicao(de, para, motivo)  # não levanta
    assert e.transicao_permitida(de, para, motivo)


def test_todas_as_demais_combinacoes_sao_rejeitadas():
    validas = {(de, para) for de, para, _ in VALIDAS}
    todas = itertools.product((None, *e.ESTADOS), e.ESTADOS)
    invalidas = [(de, para) for de, para in todas if (de, para) not in validas]
    assert len(invalidas) == 8 * 7 - 9  # 8 origens (inclui "nova") × 7 destinos − 9 válidas
    for de, para in invalidas:
        with pytest.raises(ErroNegocio) as erro:
            e.validar_transicao(de, para)
        assert erro.value.codigo == "TRANSICAO_INVALIDA" and erro.value.status == 409
        assert erro.value.detalhes == {"de": de, "para": para}


@pytest.mark.parametrize("de,para,motivo_errado", [
    (e.AGUARDANDO, e.NAO_COMPARECEU, e.ABANDONO),          # antes da 1ª chamada só vale o descarte do expediente
    (e.AGUARDANDO, e.NAO_COMPARECEU, None),
    (e.CHAMADA_NOVAMENTE, e.NAO_COMPARECEU, e.FIM_EXPEDIENTE),
    (e.CHAMADA_NOVAMENTE, e.NAO_COMPARECEU, None),
])
def test_nao_comparecimento_exige_o_motivo_certo(de, para, motivo_errado):
    with pytest.raises(ErroNegocio) as erro:
        e.validar_transicao(de, para, motivo_errado)
    assert erro.value.codigo == "TRANSICAO_INVALIDA"


def test_mensagem_diz_de_onde_para_onde():
    with pytest.raises(ErroNegocio) as erro:
        e.validar_transicao(e.AGUARDANDO, e.ATENDIDA)
    assert erro.value.mensagem == "A senha não pode ir de AGUARDANDO para ATENDIDA."


def test_estados_terminais_nao_saem_do_lugar():
    for terminal in (e.ATENDIDA, e.NAO_COMPARECEU):
        assert not any(de == terminal for de, _ in e.TRANSICOES)


def test_estados_ativos_sao_os_que_prendem_o_guiche():
    assert set(e.ESTADOS_ATIVOS) == {e.CHAMADA, e.CHAMADA_NOVAMENTE, e.EM_ATENDIMENTO}
