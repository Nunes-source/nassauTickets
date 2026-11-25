"""Sorteio do tempo de atendimento (TM) simulado, RN-07 / ADR-004."""
import random


def sortear_duracao(tipo: str, rng: random.Random | None = None) -> int:
    """Duração simulada em segundos.

    SP: 15 min ±5 (uniforme 10–20 min) · SG: 5 min ±3 (uniforme 2–8 min) ·
    SE: 1 min em 95% dos casos e 5 min em 5%.
    """
    rng = rng or random
    if tipo == "SP":
        return rng.randint(10 * 60, 20 * 60)
    if tipo == "SG":
        return rng.randint(2 * 60, 8 * 60)
    if tipo == "SE":
        return 5 * 60 if rng.random() < 0.05 else 60
    raise ValueError(f"tipo inválido: {tipo!r}")
