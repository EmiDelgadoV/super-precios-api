import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db


@pytest.fixture()
def db_session(tmp_path):
    """
    Base de datos SQLite temporal y vacia, una por test (tmp_path la crea
    y la borra sola). Reemplaza la conexion real de la app mientras dura el test.
    """
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture()
def client(db_session):
    """Cliente HTTP de prueba, ya conectado a la base temporal de arriba."""
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    """
    Registra y loguea un usuario de prueba. Devuelve el header Authorization
    listo para pasarle a cualquier pedido que necesite sesion.
    """
    email = "test@test.com"
    password = "clave1234"
    client.post("/auth/register", json={"email": email, "password": password})
    token = client.post(
        "/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
