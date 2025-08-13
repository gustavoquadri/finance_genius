from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.api import models, classes, auth
from app.db.connection import get_session

router = APIRouter()


@router.post("/registrar", response_model=classes.UsuarioOut)
def registrar(usuario: classes.UsuarioCreate, session: Session = Depends(get_session)):
    resultado = session.exec(select(models.Usuario).where(models.Usuario.email == usuario.email)).first()
    if resultado:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")

    novo_usuario = models.Usuario(
        nome=usuario.nome,
        usuario=usuario.usuario,
        email=usuario.email,
        senha_hash=auth.gerar_hash_senha(usuario.senha)
    )
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    return novo_usuario


@router.post("/login")
def login(usuario: classes.UsuarioLogin, session: Session = Depends(get_session)):
    resultado = session.exec(select(models.Usuario).where(models.Usuario.email == usuario.email)).first()
    if not resultado or not auth.verificar_senha(usuario.senha, resultado.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    token = auth.criar_token(str(resultado.id))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=classes.UsuarioOut)
def me(usuario: classes.UsuarioOut = Depends(auth.usuario_logado)):
    return usuario
