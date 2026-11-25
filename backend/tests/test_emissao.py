"""Numeração, texto da chamada e sorteio do TM (funções puras; não precisam de banco)."""
import random
from datetime import date

import pytest

from app.core.errors import ErroNegocio
from app.services import anuncio, simulacao
from app.services.emissao import formatar_numero

DIA = date(2026, 11, 27)


# ---- RN-02: YYMMDD-PPSQ ----

@pytest.mark.parametrize("tipo,seq,esperado", [
    ("SP", 1, "261127-SP001"), ("SG", 42, "261127-SG042"), ("SE", 999, "261127-SE999"), ("SP", 100, "261127-SP100"),
])
def test_formatar_numero(tipo, seq, esperado):
    numero = formatar_numero(DIA, tipo, seq)
    assert numero == esperado and len(numero) == 12


def test_data_usa_dois_digitos_de_ano_mes_e_dia():
    assert formatar_numero(date(2027, 1, 5), "SG", 7) == "270105-SG007"


def test_sequencia_acima_de_999_esgota():
    with pytest.raises(ErroNegocio) as erro:
        formatar_numero(DIA, "SP", 1000)
    assert erro.value.codigo == "SEQUENCIA_ESGOTADA" and erro.value.status == 409


@pytest.mark.parametrize("tipo,seq", [("XX", 1), ("sp", 1), ("", 1), ("SP", 0), ("SP", -3)])
def test_entradas_invalidas(tipo, seq):
    with pytest.raises(ValueError):
        formatar_numero(DIA, tipo, seq)


# ---- RF-17 / RNF-07: texto da chamada ----

@pytest.mark.parametrize("n,esperado", [
    (0, "zero"), (1, "um"), (3, "três"), (10, "dez"), (15, "quinze"), (20, "vinte"), (21, "vinte e um"),
    (99, "noventa e nove"), (100, "cem"), (101, "cento e um"), (342, "trezentos e quarenta e dois"),
    (999, "novecentos e noventa e nove"),
])
def test_por_extenso(n, esperado):
    assert anuncio.por_extenso(n) == esperado


@pytest.mark.parametrize("n", [-1, 1000])
def test_por_extenso_fora_do_intervalo(n):
    with pytest.raises(ValueError):
        anuncio.por_extenso(n)


def test_sequencial_dito_digito_a_digito():
    assert anuncio.sequencial_por_extenso(1) == "zero zero um"
    assert anuncio.sequencial_por_extenso(123) == "um dois três"


def test_texto_da_primeira_e_da_ultima_chamada_seguem_o_contrato():
    assert anuncio.texto_chamada("SP", 1, 3, False) == "Senha prioritária zero zero um, guichê três"
    assert anuncio.texto_chamada("SP", 1, 3, True) == "Última chamada. Senha prioritária zero zero um, guichê três"
    assert anuncio.texto_chamada("SG", 12, 1, False) == "Senha geral zero um dois, guichê um"
    assert anuncio.texto_chamada("SE", 40, 12, False) == "Senha exames zero quatro zero, guichê doze"


# ---- RN-07: TM simulado ----

def test_sp_sorteia_entre_10_e_20_minutos():
    rng = random.Random(1)
    duracoes = [simulacao.sortear_duracao("SP", rng) for _ in range(2000)]
    assert min(duracoes) >= 600 and max(duracoes) <= 1200
    assert 840 < sum(duracoes) / len(duracoes) < 960  # média ≈ 15 min


def test_sg_sorteia_entre_2_e_8_minutos():
    rng = random.Random(2)
    duracoes = [simulacao.sortear_duracao("SG", rng) for _ in range(2000)]
    assert min(duracoes) >= 120 and max(duracoes) <= 480
    assert 270 < sum(duracoes) / len(duracoes) < 330  # média ≈ 5 min


def test_se_dura_1_minuto_em_95_por_cento_e_5_em_5_por_cento():
    rng = random.Random(3)
    duracoes = [simulacao.sortear_duracao("SE", rng) for _ in range(20000)]
    assert set(duracoes) == {60, 300}
    assert 0.04 < duracoes.count(300) / len(duracoes) < 0.06


def test_tipo_invalido():
    with pytest.raises(ValueError):
        simulacao.sortear_duracao("XX")
