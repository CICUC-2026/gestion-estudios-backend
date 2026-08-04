from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class ModeloBase(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)


# Los modelos se importan aquí para que Alembic descubra su metadata.
from app.dominios.autenticacion import modelos as modelos_autenticacion  # noqa: E402, F401
from app.dominios.cupos import modelos as modelos_cupos  # noqa: E402, F401
from app.dominios.estudios import modelos as modelos_estudios  # noqa: E402, F401
from app.dominios.operacion import modelos as modelos_operacion  # noqa: E402, F401
from app.dominios.pacientes import modelos as modelos_pacientes  # noqa: E402, F401
from app.dominios.preseleccion import modelos as modelos_preseleccion  # noqa: E402, F401
