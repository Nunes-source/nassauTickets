from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TipoSenha = Literal["SP", "SG", "SE"]


class EmitirEntrada(BaseModel):
    tipo: TipoSenha = Field(description="SP prioritária · SG geral · SE retirada de exames.", examples=["SP"])


class SenhaEmitida(BaseModel):
    id: int
    numero: str = Field(examples=["261127-SP001"])
    tipo: TipoSenha
    sequencial: int
    estado: str = Field(examples=["AGUARDANDO"])
    emitida_em: datetime


class SenhaResumo(BaseModel):
    id: int
    numero: str
    tipo: TipoSenha
    sequencial: int
    estado: str


class GuicheRef(BaseModel):
    id: int
    numero: int


class ChamadaInfo(BaseModel):
    numero: int = Field(description="1 ou 2.")
    ultima_chamada: bool
    chamada_em: datetime


class ChamadaResposta(BaseModel):
    senha: SenhaResumo
    guiche: GuicheRef
    chamada: ChamadaInfo
    texto_chamada: str = Field(examples=["Senha prioritária zero zero um, guichê três"],
                               description="Texto para o áudio e para leitores de tela.")


class IniciarResposta(BaseModel):
    senha: SenhaResumo
    duracao_simulada_seg: int = Field(examples=[412])


class PainelItem(BaseModel):
    numero: str
    tipo: TipoSenha
    sequencial: int
    guiche: int
    chamada: int
    ultima_chamada: bool
    chamada_em: datetime


class PainelResposta(BaseModel):
    ultimas: list[PainelItem]
    atualizado_em: datetime
