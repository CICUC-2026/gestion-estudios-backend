"""Carga idempotente de pacientes y tareas completamente sintéticos."""

from sqlalchemy import select

from app.base_datos.sesion import FabricaSesiones
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.pacientes.esquemas import CrearPacienteDemo
from app.dominios.pacientes.modelos import PacienteDemo
from app.dominios.pacientes.servicio import crear_paciente

CASOS = (
    ("PX-DEMO-0001", "50–64 años", "Patología ficticia A"),
    ("PX-DEMO-0002", "65–79 años", "Patología ficticia B"),
)


def cargar() -> None:
    with FabricaSesiones() as sesion:
        usuario = sesion.scalar(select(Usuario).order_by(Usuario.creado_en))
        if not usuario:
            print("No existe usuario para crear pacientes demo.")
            return
        for codigo, rango, patologia in CASOS:
            existente = sesion.scalar(select(PacienteDemo).where(PacienteDemo.codigo == codigo))
            if existente:
                existente.archivado = False
                sesion.commit()
                continue
            crear_paciente(
                sesion,
                CrearPacienteDemo(codigo=codigo, rango_etario=rango, patologia=patologia),
                usuario,
            )
        print("Pacientes sintéticos de demostración disponibles.")


if __name__ == "__main__":
    cargar()
