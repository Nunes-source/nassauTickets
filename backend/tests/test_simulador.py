"""Partes puras do simulador (não precisam de API nem de banco)."""
import random

from tools import simulador


def test_cerca_de_5_por_cento_nao_comparecem():
    rng = random.Random(7)
    desfechos = [simulador.decidir_desfecho(rng) for _ in range(20000)]
    assert set(desfechos) == {"ATENDIDA", "NAO_COMPARECEU"}
    assert 0.04 < desfechos.count("NAO_COMPARECEU") / len(desfechos) < 0.06


def test_mistura_de_tipos_segue_os_pesos():
    rng = random.Random(11)
    tipos = [simulador.sortear_tipo(rng) for _ in range(20000)]
    assert 0.46 < tipos.count("SG") / len(tipos) < 0.54
    assert 0.29 < tipos.count("SE") / len(tipos) < 0.37
    assert 0.14 < tipos.count("SP") / len(tipos) < 0.20


def test_mesma_semente_mesmo_resultado():
    a, b = random.Random(5), random.Random(5)
    assert [simulador.sortear_tipo(a) for _ in range(50)] == [simulador.sortear_tipo(b) for _ in range(50)]


def test_placar_soma_com_seguranca():
    placar = simulador.Placar()
    placar.somar("emitidas", "SP")
    placar.somar("emitidas", "SG")
    placar.somar("erros")
    assert placar.dados["emitidas"] == 2 and placar.dados["erros"] == 1 and placar.por_tipo["SP"] == 1
