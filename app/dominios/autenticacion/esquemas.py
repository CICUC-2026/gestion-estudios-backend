import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CredencialesIngreso(BaseModel):
    correo: EmailStr
    contrasena: str = Field(min_length=1, max_length=256)


class TokenSesion(BaseModel):
    token_acceso: str
    tipo: str = "bearer"
    expira_en: datetime


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombres: str
    apellidos: str
    correo: EmailStr
    es_administrador_sistema: bool
    activo: bool
    ultimo_acceso: datetime | None
    creado_en: datetime


class CrearUsuario(BaseModel):
    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    correo: EmailStr
    contrasena_inicial: str = Field(min_length=12, max_length=256)
    es_administrador_sistema: bool = False


class CambiarEstadoUsuario(BaseModel):
    activo: bool


class CambiarContrasena(BaseModel):
    contrasena_actual: str = Field(min_length=1, max_length=256)
    contrasena_nueva: str = Field(min_length=12, max_length=256)


class SesionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    creada_en: datetime
    expira_en: datetime
    ultimo_uso_en: datetime
    revocada_en: datetime | None
    agente_usuario: str | None
    es_actual: bool = False
