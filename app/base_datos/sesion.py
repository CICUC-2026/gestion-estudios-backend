from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.configuracion.ajustes import obtener_ajustes

ajustes = obtener_ajustes()
motor = create_engine(ajustes.base_datos_url, pool_pre_ping=True)
FabricaSesiones = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def obtener_sesion() -> Generator[Session, None, None]:
    with FabricaSesiones() as sesion:
        yield sesion
