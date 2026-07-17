from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Ajustes(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CICUC_",
        extra="ignore",
    )

    nombre_aplicacion: str = "API de gestión de estudios clínicos CICUC"
    entorno: str = "desarrollo"
    base_datos_url: str = Field(
        default="postgresql+psycopg://cicuc:cicuc_demo@localhost:5432/gestion_estudios"
    )


@lru_cache
def obtener_ajustes() -> Ajustes:
    return Ajustes()
