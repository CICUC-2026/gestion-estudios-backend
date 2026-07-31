import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ.setdefault(
    "CICUC_BASE_DATOS_URL",
    "postgresql+psycopg://cicuc:cicuc_demo@127.0.0.1:5432/gestion_estudios_pruebas",
)

from app.base_datos.modelos import ModeloBase  # noqa: E402
from app.base_datos.sesion import FabricaSesiones, motor  # noqa: E402
from app.dominios.autenticacion.esquemas import CrearUsuario  # noqa: E402
from app.dominios.autenticacion.modelos import Usuario  # noqa: E402
from app.dominios.autenticacion.servicio import crear_usuario  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def base_limpia() -> Generator[None, None, None]:
    ModeloBase.metadata.drop_all(motor)
    ModeloBase.metadata.create_all(motor)
    yield
    ModeloBase.metadata.drop_all(motor)


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sesion_db() -> Generator[Session, None, None]:
    with FabricaSesiones() as sesion:
        yield sesion


@pytest.fixture
def administrador() -> Usuario:
    with FabricaSesiones() as sesion_db:
        return crear_usuario(
            sesion_db,
            CrearUsuario(
                nombres="Ada",
                apellidos="Administradora",
                correo="admin@example.com",
                contrasena_inicial="Contrasena-Demo-2026",
                es_administrador_sistema=True,
            ),
            actor_id=None,
            direccion_ip="127.0.0.1",
        )


@pytest.fixture
def token_admin(cliente: TestClient, administrador: Usuario) -> str:
    respuesta = cliente.post(
        "/api/v1/autenticacion/ingresar",
        json={"correo": administrador.correo, "contrasena": "Contrasena-Demo-2026"},
    )
    assert respuesta.status_code == 200
    return str(respuesta.json()["token_acceso"])
