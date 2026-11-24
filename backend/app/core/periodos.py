"""Cálculo de períodos de relatórios e indicadores (funções puras, fáceis de testar).

Levantam `ValueError` com mensagem clara; o service converte em erro `VALIDACAO` (422).
"""
import calendar
from datetime import date

MAX_DIAS_INTERVALO = 366


def intervalo_diario(dia: date) -> tuple[date, date, str]:
    return dia, dia, dia.isoformat()


def intervalo_mensal(ano: int, mes: int) -> tuple[date, date, str]:
    if not 1 <= mes <= 12:
        raise ValueError("mes deve estar entre 1 e 12")
    if not 2000 <= ano <= 2100:
        raise ValueError("ano deve estar entre 2000 e 2100")
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, 1), date(ano, mes, ultimo_dia), f"{ano:04d}-{mes:02d}"


def validar_intervalo(de: date, ate: date) -> None:
    if de > ate:
        raise ValueError("'de' não pode ser depois de 'ate'")
    if (ate - de).days + 1 > MAX_DIAS_INTERVALO:
        raise ValueError(f"o intervalo não pode passar de {MAX_DIAS_INTERVALO} dias")


def dias_no_intervalo(de: date, ate: date) -> int:
    return (ate - de).days + 1
