from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.usuarios import EMAIL_REGEX

Perfil = Literal["ATENDENTE", "GESTOR"]


class LoginEntrada(BaseModel):
    email: str = Field(pattern=EMAIL_REGEX, max_length=150, examples=["atendente1@nassau.local"])
    senha: str = Field(min_length=1, max_length=128, examples=["Atendente@123"])


class LoginResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_em: datetime
    perfil: Perfil
    nome: str


class GuicheDoUsuario(BaseModel):
    id: int
    numero: int


class UsuarioMe(BaseModel):
    id: int
    nome: str
    email: str
    perfil: Perfil
    guiche: GuicheDoUsuario | None = None
