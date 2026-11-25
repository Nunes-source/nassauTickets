from typing import Literal

from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
Perfil = Literal["ATENDENTE", "GESTOR"]


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=100, examples=["Maria Souza"])
    email: str = Field(pattern=EMAIL_REGEX, max_length=150, examples=["maria@nassau.local"])
    senha: str = Field(min_length=8, max_length=128, examples=["Troque@123"])
    perfil: Perfil

    @field_validator("nome")
    @classmethod
    def _nome(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("nome não pode ser vazio")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioAtualizar(BaseModel):
    """Todos os campos são opcionais; só o que for enviado é alterado."""
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, pattern=EMAIL_REGEX, max_length=150)
    senha: str | None = Field(default=None, min_length=8, max_length=128)
    perfil: Perfil | None = None
    ativo: bool | None = None

    @field_validator("email")
    @classmethod
    def _email(cls, v: str | None) -> str | None:
        return v.strip().lower() if v else v


class UsuarioSaida(BaseModel):
    id: int
    nome: str
    email: str
    perfil: Perfil
    ativo: bool
