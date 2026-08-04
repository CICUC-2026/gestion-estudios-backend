import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import auditar
from app.dominios.estudios.modelos import Estudio
from app.dominios.pacientes.esquemas import (
    ActualizarPacienteDemo,
    AsociarEstudioDemo,
    CrearDiagnosticoDemo,
    CrearPacienteDemo,
)
from app.dominios.pacientes.modelos import DiagnosticoDemo, PacienteDemo, PacienteEstudioDemo


def obtener_paciente(sesion: Session, paciente_id: uuid.UUID) -> PacienteDemo:
    paciente = sesion.get(PacienteDemo, paciente_id)
    if not paciente:
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró el paciente sintético.")
    return paciente


def crear_paciente(sesion: Session, datos: CrearPacienteDemo, usuario: Usuario) -> PacienteDemo:
    ahora = datetime.now(UTC)
    paciente = PacienteDemo(
        **datos.model_dump(),
        sintetico=True,
        archivado=False,
        creado_por_id=usuario.id,
        creado_en=ahora,
        actualizado_en=ahora,
    )
    sesion.add(paciente)
    try:
        sesion.flush()
    except IntegrityError as error:
        sesion.rollback()
        raise ErrorApi(409, "CODIGO_DUPLICADO", "El código ficticio ya está registrado.") from error
    auditar(
        sesion,
        accion="paciente_demo.crear",
        entidad="paciente_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=paciente.id,
    )
    sesion.commit()
    sesion.refresh(paciente)
    return paciente


def actualizar_paciente(
    sesion: Session, paciente: PacienteDemo, datos: ActualizarPacienteDemo, usuario: Usuario
) -> PacienteDemo:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(paciente, campo, valor)
    paciente.actualizado_en = datetime.now(UTC)
    auditar(
        sesion,
        accion="paciente_demo.actualizar",
        entidad="paciente_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=paciente.id,
        contexto=datos.model_dump(mode="json", exclude_unset=True),
    )
    sesion.commit()
    sesion.refresh(paciente)
    return paciente


def crear_diagnostico(
    sesion: Session, paciente: PacienteDemo, datos: CrearDiagnosticoDemo, usuario: Usuario
) -> DiagnosticoDemo:
    item = DiagnosticoDemo(
        **datos.model_dump(),
        paciente_id=paciente.id,
        creado_por_id=usuario.id,
        creado_en=datetime.now(UTC),
    )
    sesion.add(item)
    sesion.flush()
    auditar(
        sesion,
        accion="paciente_demo.diagnostico_crear",
        entidad="diagnostico_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=item.id,
    )
    sesion.commit()
    sesion.refresh(item)
    return item


def asociar_estudio(
    sesion: Session, paciente: PacienteDemo, datos: AsociarEstudioDemo, usuario: Usuario
) -> PacienteEstudioDemo:
    if not sesion.get(Estudio, datos.estudio_id):
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró el estudio.")
    item = PacienteEstudioDemo(
        paciente_id=paciente.id,
        estudio_id=datos.estudio_id,
        estado="pendiente_revision",
        observaciones=datos.observaciones,
        creado_por_id=usuario.id,
        creado_en=datetime.now(UTC),
    )
    sesion.add(item)
    try:
        sesion.flush()
    except IntegrityError as error:
        sesion.rollback()
        raise ErrorApi(409, "ASOCIACION_DUPLICADA", "La asociación ya existe.") from error
    auditar(
        sesion,
        accion="paciente_demo.asociar_estudio",
        entidad="paciente_estudio_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=item.id,
    )
    sesion.commit()
    sesion.refresh(item)
    return item
