"""Escolha do próximo tipo (ADR-003): tabela completa 4 (último tipo) × 8 (combinações disponíveis)."""
import pytest

from app.services.fila import escolher_tipo

SP, SE, SG = "SP", "SE", "SG"

# (ultimo_tipo, disponiveis) -> esperado. Regra: tira o último tipo dos candidatos; se não sobrar nada,
# repete o único que tem fila; entre os candidatos vale SP > SE > SG.
TABELA = {
    # primeira chamada do dia
    (None, frozenset()): None,
    (None, frozenset({SP})): SP, (None, frozenset({SE})): SE, (None, frozenset({SG})): SG,
    (None, frozenset({SP, SE})): SP, (None, frozenset({SP, SG})): SP, (None, frozenset({SE, SG})): SE,
    (None, frozenset({SP, SE, SG})): SP,
    # último foi SP
    (SP, frozenset()): None,
    (SP, frozenset({SP})): SP, (SP, frozenset({SE})): SE, (SP, frozenset({SG})): SG,
    (SP, frozenset({SP, SE})): SE, (SP, frozenset({SP, SG})): SG, (SP, frozenset({SE, SG})): SE,
    (SP, frozenset({SP, SE, SG})): SE,
    # último foi SE
    (SE, frozenset()): None,
    (SE, frozenset({SP})): SP, (SE, frozenset({SE})): SE, (SE, frozenset({SG})): SG,
    (SE, frozenset({SP, SE})): SP, (SE, frozenset({SP, SG})): SP, (SE, frozenset({SE, SG})): SG,
    (SE, frozenset({SP, SE, SG})): SP,
    # último foi SG
    (SG, frozenset()): None,
    (SG, frozenset({SP})): SP, (SG, frozenset({SE})): SE, (SG, frozenset({SG})): SG,
    (SG, frozenset({SP, SE})): SP, (SG, frozenset({SP, SG})): SP, (SG, frozenset({SE, SG})): SE,
    (SG, frozenset({SP, SE, SG})): SP,
}


def test_a_tabela_cobre_todas_as_32_combinacoes():
    assert len(TABELA) == 4 * 8


@pytest.mark.parametrize("ultimo,disponiveis,esperado", [(u, d, e) for (u, d), e in TABELA.items()],
                         ids=lambda v: "-".join(sorted(v)) if isinstance(v, frozenset) else str(v))
def test_escolher_tipo(ultimo, disponiveis, esperado):
    assert escolher_tipo(ultimo, disponiveis) == esperado


def test_aceita_qualquer_iteravel_e_nao_altera_a_entrada():
    disponiveis = [SG, SE]
    assert escolher_tipo(SE, disponiveis) == SG
    assert disponiveis == [SG, SE]
    assert escolher_tipo(None, iter([SG])) == SG


def _simular(filas: dict[str, int]) -> list[str]:
    """Esvazia as filas chamando uma senha por vez, como um dia sem concorrência."""
    restantes, ultimo, ordem = dict(filas), None, []
    while any(restantes.values()):
        tipo = escolher_tipo(ultimo, {t for t, n in restantes.items() if n})
        restantes[tipo] -= 1
        ordem.append(tipo)
        ultimo = tipo
    return ordem


def test_dia_simulado_com_as_tres_filas_cheias():
    # SG só é chamada quando SP ou SE esvaziam (consequência assumida no ADR-003)
    assert _simular({SP: 3, SE: 3, SG: 3}) == [SP, SE, SP, SE, SP, SE, SG, SG, SG]


@pytest.mark.parametrize("filas,esperado", [
    ({SP: 2, SE: 0, SG: 2}, [SP, SG, SP, SG]),        # sem SE
    ({SP: 0, SE: 2, SG: 2}, [SE, SG, SE, SG]),        # sem SP
    ({SP: 0, SE: 0, SG: 3}, [SG, SG, SG]),            # só SG
    ({SP: 1, SE: 1, SG: 0}, [SP, SE]),
])
def test_dia_simulado_com_filas_vazias(filas, esperado):
    assert _simular(filas) == esperado


def test_nunca_repete_o_tipo_enquanto_houver_outro_disponivel():
    ordem = _simular({SP: 5, SE: 4, SG: 6})
    for anterior, atual, i in zip(ordem, ordem[1:], range(len(ordem))):
        restante = {t: ordem[i + 1:].count(t) for t in (SP, SE, SG)}
        if anterior == atual:  # só pode repetir se ele era o único com fila
            assert sum(1 for n in restante.values() if n) == 1
