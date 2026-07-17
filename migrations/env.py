from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.base_datos.modelos import ModeloBase
from app.configuracion.ajustes import obtener_ajustes

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", obtener_ajustes().base_datos_url)
target_metadata = ModeloBase.metadata


def ejecutar_migraciones_sin_conexion() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def ejecutar_migraciones_con_conexion() -> None:
    conexion = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conexion.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    ejecutar_migraciones_sin_conexion()
else:
    ejecutar_migraciones_con_conexion()
