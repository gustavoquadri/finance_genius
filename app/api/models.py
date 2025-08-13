import uuid
from sqlmodel import SQLModel, Field
from datetime import date


# ========== MODELOS ==========
class Usuario(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nome: str
    usuario: str
    email: str = Field(unique=True, index=True)
    senha_hash: str
    data_criacao: date = Field(default_factory=date.today)
