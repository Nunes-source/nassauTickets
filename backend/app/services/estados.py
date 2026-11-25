"""Máquina de estados da senha (docs/models/uml/diagramas.md §3). Fonte única das transições."""
from app.core.errors import ErroNegocio

EMITIDA = "EMITIDA"
AGUARDANDO = "AGUARDANDO"
CHAMADA = "CHAMADA"
CHAMADA_NOVAMENTE = "CHAMADA_NOVAMENTE"
EM_ATENDIMENTO = "EM_ATENDIMENTO"
ATENDIDA = "ATENDIDA"
NAO_COMPARECEU = "NAO_COMPARECEU"

ESTADOS = (EMITIDA, AGUARDANDO, CHAMADA, CHAMADA_NOVAMENTE, EM_ATENDIMENTO, ATENDIDA, NAO_COMPARECEU)
ESTADOS_ATIVOS = (CHAMADA, CHAMADA_NOVAMENTE, EM_ATENDIMENTO)  # prendem o guichê (RN-12)

ABANDONO = "ABANDONO"
FIM_EXPEDIENTE = "FIM_EXPEDIENTE"

# (de, para) -> (ação, quem faz, motivo_descarte exigido ou None). `de=None` é a senha nova.
TRANSICOES: dict[tuple[str | None, str], tuple[str, str, str | None]] = {
    (None, EMITIDA): ("emitir", "TOTEM", None),
    (EMITIDA, AGUARDANDO): ("concluir emissão", "SISTEMA", None),
    (AGUARDANDO, CHAMADA): ("chamar próximo", "ATENDENTE", None),
    (AGUARDANDO, NAO_COMPARECEU): ("descarte às 17h", "SISTEMA", FIM_EXPEDIENTE),
    (CHAMADA, CHAMADA_NOVAMENTE): ("chamar novamente", "ATENDENTE", None),
    (CHAMADA, EM_ATENDIMENTO): ("iniciar", "ATENDENTE", None),
    (CHAMADA_NOVAMENTE, EM_ATENDIMENTO): ("iniciar", "ATENDENTE", None),
    (CHAMADA_NOVAMENTE, NAO_COMPARECEU): ("não compareceu", "ATENDENTE", ABANDONO),
    (EM_ATENDIMENTO, ATENDIDA): ("encerrar", "ATENDENTE", None),
}


def transicao_permitida(de: str | None, para: str, motivo: str | None = None) -> bool:
    regra = TRANSICOES.get((de, para))
    if regra is None:
        return False
    motivo_exigido = regra[2]
    return motivo_exigido is None or motivo == motivo_exigido


def validar_transicao(de: str | None, para: str, motivo: str | None = None) -> None:
    """Levanta `409 TRANSICAO_INVALIDA` se o par (de, para) [e o motivo] não estiver na tabela."""
    if not transicao_permitida(de, para, motivo):
        origem = de or "(nova)"
        raise ErroNegocio("TRANSICAO_INVALIDA", f"A senha não pode ir de {origem} para {para}.", 409,
                          {"de": de, "para": para})
