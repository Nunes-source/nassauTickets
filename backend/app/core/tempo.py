"""Único lugar que sabe "que horas são". Fuso fixo America/Recife (nunca `datetime.now()` solto)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_config

FUSO = ZoneInfo("America/Recife")


def agora() -> datetime:
    return datetime.now(FUSO)


def hoje() -> date:
    return agora().date()


def agora_sem_fuso() -> datetime:
    """Horário de Recife como o MySQL guarda (DATETIME sem fuso), sem microssegundos
    (o MySQL arredondaria para cima e a hora gravada poderia ficar 1 s à frente)."""
    return agora().replace(microsecond=0, tzinfo=None)


def _hora_local(momento: datetime):
    if momento.tzinfo is not None:
        momento = momento.astimezone(FUSO)
    return momento.time()


def dentro_do_expediente(momento: datetime | None = None) -> bool:
    """True se `momento` (padrão: agora) está em [EXPEDIENTE_INICIO, EXPEDIENTE_FIM).

    `EXPEDIENTE_FORCAR_ABERTO=true` (só para demonstração, ADR-004) vale apenas quando
    `momento` não é informado, isto é, para o "agora" real.
    """
    config = get_config()
    if momento is None:
        if config.expediente_forcar_aberto:
            return True
        momento = agora()
    return config.expediente_inicio <= _hora_local(momento) < config.expediente_fim


def depois_do_expediente(momento: datetime | None = None) -> bool:
    """True se já passou do fim do expediente no dia (dispara o descarte, RN-10)."""
    config = get_config()
    if momento is None:
        if config.expediente_forcar_aberto:
            return False
        momento = agora()
    return _hora_local(momento) >= config.expediente_fim


def horas_de_expediente() -> float:
    """Duração do expediente em horas (usada na vazão por hora)."""
    config = get_config()
    inicio = config.expediente_inicio.hour * 60 + config.expediente_inicio.minute
    fim = config.expediente_fim.hour * 60 + config.expediente_fim.minute
    return (fim - inicio) / 60


def com_fuso(valor: datetime | None) -> datetime | None:
    """O banco guarda DATETIME sem fuso (horário de Recife). Ao responder, anexamos o fuso."""
    if valor is None:
        return None
    return valor.replace(tzinfo=FUSO) if valor.tzinfo is None else valor.astimezone(FUSO)
