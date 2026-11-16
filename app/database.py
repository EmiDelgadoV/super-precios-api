import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# "or" en vez del valor por defecto de getenv: si la variable existe pero esta
# vacia, tambien se usa SQLite en lugar de fallar.
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./superprecios.db"

# Los servicios de hosting (Render, Railway, etc.) entregan la URL de la base como
# "postgres://..." o "postgresql://...", sin indicar el driver. SQLAlchemy
# necesita el driver explicito: aca se usa psycopg 3, el de requirements.txt.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

# pool_pre_ping: antes de usar una conexion del pool, verifica que siga viva.
# Las bases gestionadas cierran conexiones inactivas; sin esto, el primer
# pedido despues de un rato quieto podria fallar.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
