"""Único lugar que sabe "que horas são". Fuso fixo America/Recife (nunca `datetime.now()` solto)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_config

FUSO = ZoneInfo("America/Recife")


def agora() -> datetime:
    return datetime.now(FUSO)


def hoje() -> date:
    return agora().date()


def dentro_do_expediente(momento: datetime | None = None) -> bool:
    """True se `momento` (padrão: agora) está em [EXPEDIENTE_INICIO, EXPEDIENTE_FIM)."""
    momento = momento or agora()
    if momento.tzinfo is not None:
        momento = momento.astimezone(FUSO)
    config = get_config()
    return config.expediente_inicio <= momento.time() < config.expediente_fim


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
