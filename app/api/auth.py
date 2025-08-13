from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.connection import get_session
from sqlmodel import Session, select
from app.api.models import Usuario
from passlib.hash import bcrypt
from jose import jwt, JWTError

SECRET_KEY = "gtv"
ALGORITHM = "HS256"

security = HTTPBearer()


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hash(senha)


def verificar_senha(senha: str, hash: str) -> bool:
    return bcrypt.verify(senha, hash)


def criar_token(user_id: int) -> str:
    return jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        return None


def usuario_logado(cred: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session)) -> Usuario:
    try:
        token = cred.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = session.exec(select(Usuario).where(Usuario.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return user
