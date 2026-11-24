from datetime import date

import pytest

from app.core import periodos


def test_intervalo_diario():
    assert periodos.intervalo_diario(date(2026, 11, 27)) == (date(2026, 11, 27), date(2026, 11, 27), "2026-11-27")


def test_intervalo_mensal_conhece_o_ultimo_dia():
    assert periodos.intervalo_mensal(2026, 11) == (date(2026, 11, 1), date(2026, 11, 30), "2026-11")
    assert periodos.intervalo_mensal(2028, 2)[1] == date(2028, 2, 29)  # bissexto
    assert periodos.intervalo_mensal(2026, 2)[1] == date(2026, 2, 28)


@pytest.mark.parametrize("ano,mes", [(2026, 0), (2026, 13), (1999, 5), (2101, 5)])
def test_intervalo_mensal_invalido(ano, mes):
    with pytest.raises(ValueError):
        periodos.intervalo_mensal(ano, mes)


def test_validar_intervalo():
    periodos.validar_intervalo(date(2026, 11, 1), date(2026, 11, 30))
    with pytest.raises(ValueError):
        periodos.validar_intervalo(date(2026, 11, 30), date(2026, 11, 1))
    with pytest.raises(ValueError):
        periodos.validar_intervalo(date(2025, 1, 1), date(2026, 12, 31))  # mais de 366 dias


def test_dias_no_intervalo_conta_os_dois_extremos():
    assert periodos.dias_no_intervalo(date(2026, 11, 27), date(2026, 11, 27)) == 1
    assert periodos.dias_no_intervalo(date(2026, 11, 1), date(2026, 11, 30)) == 30
