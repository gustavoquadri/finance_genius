from sqlmodel import Session, create_engine
from app.src.config import DATABASE_URL


engine = create_engine(DATABASE_URL, echo=True, echo_pool='debug')


def get_session():
    with Session(engine) as session:
        yield session
