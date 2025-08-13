from pydantic import BaseModel
from uuid import UUID


class UsuarioCreate(BaseModel):
    nome: str
    usuario: str
    email: str
    senha: str


class UsuarioLogin(BaseModel):
    email: str
    senha: str


class UsuarioOut(BaseModel):
    id: UUID
    usuario: str
    nome: str
    email: str

    # class Config:
    #     orm_mode = True
    class Config:
        from_attributes = True
