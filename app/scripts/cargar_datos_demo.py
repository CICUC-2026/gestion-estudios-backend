from sqlalchemy import select

from app.base_datos.modelos import ModeloBase
from app.base_datos.sesion import FabricaSesiones, motor
from app.dominios.autenticacion.esquemas import CrearUsuario
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.autenticacion.servicio import crear_usuario, normalizar_correo
from app.dominios.estudios.esquemas import CrearEstudio, CrearVersionProtocolo
from app.dominios.estudios.servicio import crear_estudio, crear_version_protocolo


def sembrar_datos() -> None:
    print("Creando tablas si no existen...")
    ModeloBase.metadata.create_all(bind=motor)
    with FabricaSesiones() as sesion:
        # 1. Crear Administrador
        correo_admin = normalizar_correo("admin@cicuc.cl")
        admin = sesion.scalar(select(Usuario).where(Usuario.correo == correo_admin))
        if not admin:
            admin = crear_usuario(
                sesion,
                CrearUsuario(
                    nombres="Administrador",
                    apellidos="CICUC",
                    correo="admin@cicuc.cl",
                    contrasena_inicial="AdminCicuc2026!",
                    es_administrador_sistema=True,
                    roles=[RolUsuario.ADMINISTRADOR, RolUsuario.COORDINADOR],
                ),
                actor_id=None,
                direccion_ip="127.0.0.1",
            )
            print("Usuario administrador creado: admin@cicuc.cl")
        else:
            print("Usuario administrador ya existia: admin@cicuc.cl")

        # 2. Crear Investigador Principal
        correo_pi = normalizar_correo("investigador@cicuc.cl")
        pi = sesion.scalar(select(Usuario).where(Usuario.correo == correo_pi))
        if not pi:
            pi = crear_usuario(
                sesion,
                CrearUsuario(
                    nombres="Dr. Roberto",
                    apellidos="Silva",
                    correo="investigador@cicuc.cl",
                    contrasena_inicial="Investigador2026!",
                    roles=[RolUsuario.INVESTIGADOR_PRINCIPAL],
                ),
                actor_id=admin.id,
                direccion_ip="127.0.0.1",
            )
            print("Usuario PI creado: investigador@cicuc.cl")

        # 3. Crear Estudio de Demostración (MK-1084-014)
        estudio = crear_estudio(
            sesion,
            CrearEstudio(
                codigo_interno="EST-001",
                titulo="Estudio Fase 3 KANDLELIT-014 en Cáncer Colorrectal Avanzado KRAS G12C",
                patologia="Cáncer Colorrectal",
                escenario_clinico="Metastásico",
                fase="Fase 3",
                patrocinador="MSD",
                linea_tratamiento="Segunda línea",
                centro_atencion="CICUC San Joaquín",
                coordinador_id=admin.id,
                investigador_principal_id=pi.id if pi else None,
            ),
            actor_id=admin.id,
            direccion_ip="127.0.0.1",
        )
        print(f"Estudio demo creado: {estudio.codigo_interno}")

        # 4. Crear Versión de Protocolo inicial
        version = crear_version_protocolo(
            sesion,
            estudio,
            CrearVersionProtocolo(
                numero_version="v1.0",
                descripcion_cambios="Versión inicial del protocolo oficial MK-1084-014",
            ),
            actor_id=admin.id,
            direccion_ip="127.0.0.1",
        )
        print(f"Versión de protocolo creada: {version.numero_version}")

    print("Sembrado completado con éxito.")


if __name__ == "__main__":
    sembrar_datos()
