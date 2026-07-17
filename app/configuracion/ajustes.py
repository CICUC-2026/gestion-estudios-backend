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
    duracion_sesion_minutos: int = Field(default=480, ge=5, le=43_200)
    maximo_intentos_fallidos: int = Field(default=5, ge=2, le=20)
    bloqueo_minutos: int = Field(default=15, ge=1, le=1_440)
    origenes_frontend: str = "http://localhost:5173"

    @property
    def lista_origenes_frontend(self) -> list[str]:
        return [origen.strip() for origen in self.origenes_frontend.split(",") if origen.strip()]


@lru_cache
def obtener_ajustes() -> Ajustes:
    return Ajustes()
