import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.dominios.autenticacion.dependencias import SesionDb, UsuarioActual, requerir_roles
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.pacientes.esquemas import (
    ActualizarPacienteDemo,
    AsociarEstudioDemo,
    CrearDiagnosticoDemo,
    CrearPacienteDemo,
    DiagnosticoDemoRespuesta,
    PacienteDemoRespuesta,
    PacienteEstudioDemoRespuesta,
)
from app.dominios.pacientes.modelos import DiagnosticoDemo, PacienteDemo, PacienteEstudioDemo
from app.dominios.pacientes.servicio import (
    actualizar_paciente,
    asociar_estudio,
    crear_diagnostico,
    crear_paciente,
    obtener_paciente,
)

router = APIRouter(prefix="/pacientes-demo", tags=["pacientes demo"])
GestionPaciente = Annotated[
    Usuario,
    Depends(
        requerir_roles(
            RolUsuario.MEDICO_INVESTIGADOR,
            RolUsuario.COORDINADOR,
            RolUsuario.INVESTIGADOR_PRINCIPAL,
        )
    ),
]


@router.get("", response_model=list[PacienteDemoRespuesta])
def listar(
    sesion: SesionDb, _: UsuarioActual, incluir_archivados: bool = False
) -> list[PacienteDemo]:
    consulta = select(PacienteDemo).order_by(PacienteDemo.creado_en.desc())
    if not incluir_archivados:
        consulta = consulta.where(PacienteDemo.archivado.is_(False))
    return list(sesion.scalars(consulta).all())


@router.post("", response_model=PacienteDemoRespuesta, status_code=201)
def registrar(datos: CrearPacienteDemo, sesion: SesionDb, usuario: GestionPaciente) -> PacienteDemo:
    return crear_paciente(sesion, datos, usuario)


@router.get("/{paciente_id}", response_model=PacienteDemoRespuesta)
def detalle(paciente_id: uuid.UUID, sesion: SesionDb, _: UsuarioActual) -> PacienteDemo:
    return obtener_paciente(sesion, paciente_id)


@router.patch("/{paciente_id}", response_model=PacienteDemoRespuesta)
def modificar(
    paciente_id: uuid.UUID,
    datos: ActualizarPacienteDemo,
    sesion: SesionDb,
    usuario: GestionPaciente,
) -> PacienteDemo:
    return actualizar_paciente(sesion, obtener_paciente(sesion, paciente_id), datos, usuario)


@router.get("/{paciente_id}/diagnosticos", response_model=list[DiagnosticoDemoRespuesta])
def listar_diagnosticos(
    paciente_id: uuid.UUID, sesion: SesionDb, _: UsuarioActual
) -> list[DiagnosticoDemo]:
    obtener_paciente(sesion, paciente_id)
    return list(
        sesion.scalars(
            select(DiagnosticoDemo)
            .where(DiagnosticoDemo.paciente_id == paciente_id)
            .order_by(DiagnosticoDemo.fecha.desc())
        ).all()
    )


@router.post(
    "/{paciente_id}/diagnosticos", response_model=DiagnosticoDemoRespuesta, status_code=201
)
def registrar_diagnostico(
    paciente_id: uuid.UUID, datos: CrearDiagnosticoDemo, sesion: SesionDb, usuario: GestionPaciente
) -> DiagnosticoDemo:
    return crear_diagnostico(sesion, obtener_paciente(sesion, paciente_id), datos, usuario)


@router.get("/{paciente_id}/estudios", response_model=list[PacienteEstudioDemoRespuesta])
def listar_estudios(
    paciente_id: uuid.UUID, sesion: SesionDb, _: UsuarioActual
) -> list[PacienteEstudioDemo]:
    obtener_paciente(sesion, paciente_id)
    return list(
        sesion.scalars(
            select(PacienteEstudioDemo)
            .where(PacienteEstudioDemo.paciente_id == paciente_id)
            .order_by(PacienteEstudioDemo.creado_en.desc())
        ).all()
    )


@router.post(
    "/{paciente_id}/estudios", response_model=PacienteEstudioDemoRespuesta, status_code=201
)
def registrar_estudio(
    paciente_id: uuid.UUID, datos: AsociarEstudioDemo, sesion: SesionDb, usuario: GestionPaciente
) -> PacienteEstudioDemo:
    return asociar_estudio(sesion, obtener_paciente(sesion, paciente_id), datos, usuario)
