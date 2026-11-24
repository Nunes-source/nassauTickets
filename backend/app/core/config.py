"""Configuração lida do ambiente (arquivo .env). Nenhum segredo fica no código."""
import os
from dataclasses import dataclass
from datetime import time
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _hora(valor: str) -> time:
    horas, minutos = valor.split(":")
    return time(int(horas), int(minutos))


@dataclass(frozen=True)
class Config:
    db_host: str
    db_porta: int
    db_nome: str
    db_usuario: str
    db_senha: str
    jwt_segredo: str
    jwt_expira_min: int
    cors_origens: list[str]
    expediente_inicio: time
    expediente_fim: time
    log_nivel: str


@lru_cache
def get_config() -> Config:
    """Lê o ambiente uma vez. Nos testes, chame `get_config.cache_clear()` após mudar variáveis."""
    segredo = os.getenv("JWT_SECRET", "")
    if len(segredo) < 16:
        raise RuntimeError("JWT_SECRET ausente ou curto demais (mínimo 16 caracteres). Veja .env.example.")
    origens = [o.strip() for o in os.getenv("CORS_ORIGENS", "http://localhost:5173").split(",") if o.strip()]
    return Config(
        db_host=os.getenv("DB_HOST", "localhost"),
        db_porta=int(os.getenv("DB_PORT", "3306")),
        db_nome=os.getenv("DB_NAME", "nassau_tickets"),
        db_usuario=os.getenv("DB_USER", "nassau"),
        db_senha=os.getenv("DB_PASSWORD", ""),
        jwt_segredo=segredo,
        jwt_expira_min=int(os.getenv("JWT_EXPIRA_MIN", "480")),
        cors_origens=origens,
        expediente_inicio=_hora(os.getenv("EXPEDIENTE_INICIO", "07:00")),
        expediente_fim=_hora(os.getenv("EXPEDIENTE_FIM", "17:00")),
        log_nivel=os.getenv("LOG_NIVEL", "INFO").upper(),
    )
