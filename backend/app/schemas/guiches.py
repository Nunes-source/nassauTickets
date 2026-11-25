from pydantic import BaseModel, Field


class Ocupante(BaseModel):
    id: int
    nome: str


class GuicheSaida(BaseModel):
    id: int
    numero: int
    ativo: bool
    livre: bool = Field(description="Ativo e sem atendente.")
    ocupante: Ocupante | None = None


class GuicheCriar(BaseModel):
    numero: int = Field(ge=1, le=999, examples=[4])


class GuicheAtualizar(BaseModel):
    ativo: bool
