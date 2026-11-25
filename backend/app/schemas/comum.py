"""Modelos e atalhos compartilhados pela documentação Swagger."""
from pydantic import BaseModel, Field


class ErroResposta(BaseModel):
    codigo: str = Field(examples=["TRANSICAO_INVALIDA"])
    mensagem: str = Field(examples=["A senha não pode ir de AGUARDANDO para ATENDIDA."])
    detalhes: dict = Field(default_factory=dict)
    request_id: str = Field(examples=["b1f4c2d09a7e4f0e8f1c5a2b3d4e5f60"])


_DESCRICOES = {
    401: "Não autenticado (`NAO_AUTENTICADO`) ou credenciais inválidas (`CREDENCIAIS_INVALIDAS`).",
    403: "Perfil sem permissão (`SEM_PERMISSAO`).",
    404: "Recurso inexistente (`NAO_ENCONTRADO`).",
    409: "Conflito com uma regra de negócio; veja o campo `codigo`.",
    422: "Corpo ou parâmetro inválido (`VALIDACAO`); os campos vêm em `detalhes`.",
    503: "Banco indisponível (`BANCO_INDISPONIVEL`); o cabeçalho `Retry-After` indica quando tentar de novo.",
}


def respostas(*status: int) -> dict:
    """Monta o bloco `responses=` do FastAPI com o formato de erro padrão."""
    return {s: {"model": ErroResposta, "description": _DESCRICOES[s]} for s in status}
