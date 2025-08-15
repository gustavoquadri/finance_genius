from fastapi import FastAPI
from app.db.connection import engine
from sqlmodel import SQLModel
from app.api.routers import usuarios
from contextlib import asynccontextmanager

# uvicorn app.api.general:app --reload


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Finance Genius",
    description="API para gerenciamento de usuários e coleta de informações de ativos",
    version="0.0.1"
    )


@app.get("/")
def read_root():
    return {"message": "Ta rodando!"}


app.include_router(usuarios.router, prefix="/usuarios")
